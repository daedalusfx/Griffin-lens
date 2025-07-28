# frontend/data_model.py
# The intelligent data model that acts as the brain of the dashboard.

import time
import json
import numpy as np
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal

class BrokerDataModel(QObject):
    """
    Manages all live data, performs calculations, and emits signals
    when the state changes. This is the "Model" in our Model-View architecture.
    """
    # Signals that the View (Dashboard) will connect to.
    stats_updated = pyqtSignal(dict)
    events_updated = pyqtSignal(list)
    chart_data_updated = pyqtSignal(str, float)

    def __init__(self):
        super().__init__()
        self.broker_states = {}
        self.critical_events = deque(maxlen=50)

    def process_json_message(self, json_message):
        """
        The single entry point for new data from the WebSocket.
        This method updates the internal state and emits signals.
        """
        try:
            data = json.loads(json_message)
            stats = data.get("stats", {})
            events = data.get("events", [])

            # Emit signals with the new, processed data
            if stats:
                self.stats_updated.emit(stats)
                for broker, broker_stats in stats.items():
                    self.chart_data_updated.emit(broker, broker_stats['current_spread'])
            
            if events:
                # We only update if there are new events to avoid unnecessary redraws
                if len(events) > len(self.critical_events):
                    self.critical_events = deque(events, maxlen=50)
                    self.events_updated.emit(list(self.critical_events))

        except json.JSONDecodeError:
            print(f"Could not decode JSON message: {json_message}")
        except Exception as e:
            print(f"Error processing message in data model: {e}")

