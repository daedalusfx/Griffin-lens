import sys
import asyncio
import websockets
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QStyledItemDelegate, QStyle, QListWidget, QListWidgetItem, QStyleOptionProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, pyqtSlot
from PyQt6.QtGui import QColor
import pyqtgraph as pg
from collections import deque

# Import the new data model
from data_model import BrokerDataModel

# --- Configuration ---
WEBSOCKET_URI = "ws://127.0.0.1:5000/ws"
MAX_DATA_POINTS = 200

pg.setConfigOption('background', '#2E3440')
pg.setConfigOption('foreground', '#D8DEE9')

# --- Custom Table Delegate for Quality Score Bar ---
class QualityScoreDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        try:
            score = float(index.model().data(index))
            red = int(255 * (100 - score) / 100)
            green = int(255 * score / 100)
            color = QColor(red, green, 0)

            # FIX: QStyleOptionProgressBar must be imported from QtWidgets
            progress_bar_option = QStyleOptionProgressBar()
            progress_bar_option.rect = option.rect
            progress_bar_option.minimum = 0
            progress_bar_option.maximum = 100
            progress_bar_option.progress = int(score)
            progress_bar_option.text = f"{score:.1f}"
            progress_bar_option.textAlignment = Qt.AlignmentFlag.AlignCenter
            
            palette = option.palette
            palette.setColor(palette.ColorRole.Highlight, color)
            progress_bar_option.palette = palette
            
            QApplication.style().drawControl(QStyle.ControlElement.CE_ProgressBar, progress_bar_option, painter)
        except (ValueError, TypeError):
            super().paint(painter, option, index)

# --- WebSocket Client Thread ---
class WebSocketClientThread(QThread):
    new_data_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True

    async def run_client(self):
        while self.running:
            try:
                async with websockets.connect(WEBSOCKET_URI) as websocket:
                    print("Dashboard client connected to server.")
                    async for message in websocket:
                        if self.running:
                            self.new_data_signal.emit(message)
                        else:
                            break
            except Exception as e:
                print(f"WebSocket connection error: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_client())

    def stop(self):
        self.running = False
        print("Stopping WebSocket client thread...")

# --- Main Dashboard Window ---
class LiveDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Griffin Live Dashboard v2.2 - MVC Architecture")
        self.setGeometry(200, 200, 1600, 800)

        # --- Data Storage and Model ---
        self.data_model = BrokerDataModel()
        self.chart_data = {} 
        self.plot_curves = {}
        self.plot_colors = ['#88C0D0', '#A3BE8C', '#EBCB8B', '#BF616A', '#B48EAD']

        self.init_ui()
        self.apply_stylesheet()
        self.connect_signals()
        self.start_client()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        title = QLabel("Griffin Live Analysis")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #88C0D0; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content_layout = QHBoxLayout()
        
        # --- NEW: Quality Trend Chart ---
        charts_group = QGroupBox("Live Quality Score Trend")
        charts_layout = QVBoxLayout()
        self.quality_plot = pg.PlotWidget()
        self.quality_plot.setLabel('left', 'Quality Score (0-100)')
        self.quality_plot.setLabel('bottom', 'Time (Updates)')
        self.quality_plot.showGrid(x=True, y=True)
        self.quality_plot.addLegend()
        self.quality_plot.setYRange(0, 105) # Fixed Y-axis for score
        charts_layout.addWidget(self.quality_plot)
        charts_group.setLayout(charts_layout)

        right_panel = QVBoxLayout()
        
        stats_group = QGroupBox("Live Statistics Panel")
        stats_layout = QVBoxLayout()
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(5)
        self.stats_table.setHorizontalHeaderLabels([
            "Broker", "Avg Spread (10s)", "Spread Stability", "Ticks / sec", "Quality Score"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setItemDelegateForColumn(4, QualityScoreDelegate(self))
        stats_layout.addWidget(self.stats_table)
        stats_group.setLayout(stats_layout)

        events_group = QGroupBox("Critical Events")
        events_layout = QVBoxLayout()
        self.events_list = QListWidget()
        events_layout.addWidget(self.events_list)
        events_group.setLayout(events_layout)
        events_group.setFixedHeight(250)

        right_panel.addWidget(stats_group)
        right_panel.addWidget(events_group)
        
        content_layout.addWidget(charts_group)
        content_layout.addLayout(right_panel)
        main_layout.addWidget(title)
        main_layout.addLayout(content_layout)

    def connect_signals(self):
        """Connect signals from the data model to the UI update slots."""
        self.data_model.stats_updated.connect(self.update_stats_panel)
        self.data_model.events_updated.connect(self.update_events_panel)
        self.data_model.chart_data_updated.connect(self.update_quality_chart)

    def start_client(self):
        self.ws_thread = WebSocketClientThread()
        # The thread now sends data directly to the model
        self.ws_thread.new_data_signal.connect(self.data_model.process_json_message)
        self.ws_thread.start()

    @pyqtSlot(dict)
    def update_stats_panel(self, stats):
        sorted_brokers = sorted(stats.keys())
        self.stats_table.setRowCount(len(sorted_brokers))

        for i, broker in enumerate(sorted_brokers):
            broker_stats = stats[broker]
            self.stats_table.setItem(i, 0, QTableWidgetItem(broker))
            self.stats_table.setItem(i, 1, QTableWidgetItem(f"{broker_stats['avg_spread_10s']:,.1f}"))
            self.stats_table.setItem(i, 2, QTableWidgetItem(f"{broker_stats['spread_stability']:,.2f}"))
            self.stats_table.setItem(i, 3, QTableWidgetItem(f"{broker_stats['ticks_per_sec']:.1f}"))
            self.stats_table.setItem(i, 4, QTableWidgetItem(f"{broker_stats['quality_score']:.1f}"))

    @pyqtSlot(list)
    def update_events_panel(self, events):
        self.events_list.clear()
        for event in reversed(events):
            timestamp = datetime.fromtimestamp(event['time']).strftime('%H:%M:%S')
            message = f"[{timestamp}] {event['message']}"
            item = QListWidgetItem(message)
            if event['type'] == 'error':
                item.setForeground(QColor("#BF616A"))
            elif event['type'] == 'warning':
                item.setForeground(QColor("#EBCB8B"))
            self.events_list.addItem(item)
            
    @pyqtSlot(str, float)
    def update_quality_chart(self, broker, quality_score):
        if broker not in self.chart_data:
            self.chart_data[broker] = deque(maxlen=MAX_DATA_POINTS)
            color = self.plot_colors[len(self.plot_curves) % len(self.plot_colors)]
            self.plot_curves[broker] = self.quality_plot.plot(pen=pg.mkPen(color, width=2), name=broker)

        self.chart_data[broker].append(quality_score)
        self.plot_curves[broker].setData(list(self.chart_data[broker]))

    def closeEvent(self, event):
        self.ws_thread.stop()
        self.ws_thread.quit()
        self.ws_thread.wait()
        event.accept()

    def apply_stylesheet(self):
        qss = """
            QWidget { background-color: #2E3440; color: #D8DEE9; font-size: 14px; }
            QGroupBox { border: 1px solid #4C566A; border-radius: 5px; margin-top: 1ex; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }
            QTableWidget { background-color: #3B4252; border: 1px solid #4C566A; gridline-color: #4C566A; }
            QHeaderView::section { background-color: #434C5E; padding: 4px; border: 1px solid #4C566A; font-weight: bold; }
            QListWidget { background-color: #3B4252; border: 1px solid #4C566A; border-radius: 4px; }
        """
        self.setStyleSheet(qss)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LiveDashboard()
    window.show()
    sys.exit(app.exec())
