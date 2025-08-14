import sys
import os
import psutil  # اضافه شد
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox
)
from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QIcon

class GriffinLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.pid = None  # برای نگهداری Process ID

        self.setWindowTitle("Griffin Engine Launcher")
        self.setGeometry(300, 300, 700, 450)
        self.setWindowIcon(QIcon())

        self.init_ui()
        self.apply_stylesheet()

    def init_ui(self):
        # این بخش بدون تغییر باقی می‌ماند
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        control_group = QGroupBox("Engine Control")
        control_layout = QHBoxLayout()
        
        self.status_label = QLabel("Status: <font color='#EBCB8B'>Stopped</font>")
        self.status_label.setStyleSheet("font-weight: bold;")

        self.start_button = QPushButton("🚀 Start Engine")
        self.start_button.setFixedSize(150, 40)
        self.start_button.clicked.connect(self.start_server)

        self.stop_button = QPushButton("🛑 Stop Engine")
        self.stop_button.setFixedSize(150, 40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_server)

        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_group.setLayout(control_layout)

        console_group = QGroupBox("Live Console Output")
        console_layout = QVBoxLayout()
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        console_layout.addWidget(self.output_console)
        console_group.setLayout(console_layout)

        main_layout.addWidget(control_group)
        main_layout.addWidget(console_group)

    def start_server(self):
        if self.process is None:
            self.output_console.clear()
            self.output_console.append(">>> Starting Griffin Engine...")

            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.process_finished)
            
            python_executable = sys.executable
            # **تغییر مهم:** برای جلوگیری از مشکلات reload، آن را غیرفعال می‌کنیم
            # uvicorn باید در main.py با reload=False اجرا شود تا این کار کند
            # یا می‌توانیم مستقیم uvicorn را بدون reload صدا بزنیم
            script_path = os.path.join(os.path.dirname(__file__), "main.py")
            self.process.start(python_executable, [script_path])
            
            # **تغییر مهم:** PID فرآیند را ذخیره می‌کنیم
            if not self.process.waitForStarted():
                self.output_console.append("<font color='#BF616A'>ERROR: Failed to start the process.</font>")
                self.process = None
                return

            self.pid = self.process.processId()
            self.output_console.append(f">>> Engine started with PID: {self.pid}")

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_label.setText("Status: <font color='#A3BE8C'>Running</font>")

    def stop_server(self):
        # **بخش کلیدی جدید با استفاده از psutil**
        if self.pid is None:
            return

        self.output_console.append(f">>> Attempting to stop process tree with root PID: {self.pid}...")
        try:
            parent = psutil.Process(self.pid)
            # ابتدا تمام فرزندان را متوقف کن
            children = parent.children(recursive=True)
            for child in children:
                self.output_console.append(f">>> Stopping child process PID: {child.pid}")
                child.kill()
            
            # سپس خود والد را متوقف کن
            self.output_console.append(f">>> Stopping parent process PID: {parent.pid}")
            parent.kill()
            
            self.output_console.append(">>> Process tree stopped successfully.")
        except psutil.NoSuchProcess:
            self.output_console.append(">>> Process was already stopped.")
        except Exception as e:
            self.output_console.append(f"<font color='#BF616A'>ERROR stopping process: {e}</font>")
        finally:
            # 상태 재설정
            if self.process:
                self.process.kill() # برای اطمینان بیشتر
                self.process.waitForFinished()
            self.process = None
            self.pid = None
            self.process_finished() # آپدیت کردن UI

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode().strip()
        self.output_console.append(data)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode().strip()
        if "INFO:" in data:
            self.output_console.append(data)
        else:
            self.output_console.append(f"<font color='#BF616A'>ERROR: {data}</font>")

    def process_finished(self):
        # این تابع UI را بعد از توقف فرآیند آپدیت می‌کند
        if self.pid is not None: # اگر توسط stop_server متوقف نشده بود
             self.output_console.append(">>> Engine stopped unexpectedly.")
        self.pid = None
        self.process = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Status: <font color='#EBCB8B'>Stopped</font>")
    
    def closeEvent(self, event):
        # هنگام بستن پنجره، تابع جدید stop_server را صدا بزن
        self.stop_server()
        event.accept()

    def apply_stylesheet(self):
        # این بخش بدون تغییر باقی می‌ماند
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #2E3440; color: #D8DEE9; font-size: 14px; }
            QGroupBox { border: 1px solid #4C566A; border-radius: 5px; margin-top: 1ex; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }
            QTextEdit { background-color: #3B4252; border: 1px solid #4C566A; font-family: Consolas, 'Courier New', monospace; }
            QPushButton { background-color: #434C5E; color: #ECEFF4; border: 1px solid #4C566A; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #4C566A; }
            QPushButton:pressed { background-color: #5E81AC; }
            QPushButton:disabled { background-color: #3B4252; color: #4C566A; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GriffinLauncher()
    window.show()
    sys.exit(app.exec())