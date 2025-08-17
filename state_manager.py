# state_manager.py
# v13.1: Added real-time spread return for WebSocket broadcasting.

import time
import re
from typing import Dict, List, Deque, Any
from collections import deque
import math
from fastapi import Request
import numpy as np

from config import (
    TICK_BUFFER_SIZE, DYNAMIC_THRESHOLD_STD_FACTOR, PENALTY_DECAY_INTERVAL,
    PENALTY_DECAY_RATE, MAX_SCORE_HISTORY_RECORDS
)

instrument_states: Dict[str, Dict[str, 'BrokerState']] = {}
latest_analysis_results = {}
def normalize_symbol(symbol: str) -> str:
    match = re.match(r"([A-Z]{6})", symbol.upper())
    return match.group(1) if match else re.sub(r'[^A-Z0-9]', '', symbol.upper())
def sanitize_price_string(price_str: str) -> str:
    if not price_str: return "0.0"
    return re.sub(r'[^\d.]', '', price_str)

# --- BrokerState Class (v13.1) ---
class BrokerState:
    def __init__(self, broker_name: str, symbol: str):
        self.broker_name = broker_name
        self.symbol = symbol
        self.last_update_time = time.time()
        self.ticks: Deque[Dict[str, Any]] = deque(maxlen=TICK_BUFFER_SIZE)
        self.potential_glitches: List[Dict[str, Any]] = []
        self.penalty_score = 0.0
        self.last_penalty_decay_time = time.time()

        self.is_leader = False
        self.spread_samples: Deque[float] = deque(maxlen=200)

        self.quality_score_history: Deque[tuple[float, float]] = deque(maxlen=MAX_SCORE_HISTORY_RECORDS)

        self.verified_glitches: Deque[Dict[str, Any]] = deque(maxlen=100)
        self.slippage_samples: Deque[Dict[str, float]] = deque(maxlen=200)
        self.latency_samples: Deque[float] = deque(maxlen=100)
        self.tick_intervals: Deque[float] = deque(maxlen=200)
        self.last_tick_time = None
        self.correlation_with_leader = 0.5
        self.current_spread = 0.0

    def add_score_to_history(self, score: float, timestamp: float):
        """Adds a new score with its timestamp to the history."""
        self.quality_score_history.append((timestamp, score))

    def add_tick(self, bid: float, ask: float, timestamp: float) -> float:
        """
        Processes a new tick and returns the current spread.
        """
        self.last_update_time = timestamp
        if self.last_tick_time:
            self.tick_intervals.append(timestamp - self.last_tick_time)
        self.last_tick_time = timestamp

        if ask > bid:
            spread = (ask - bid) * 100000
            self.current_spread = spread # ذخیره اسپرد لحظه‌ای
            price_change = abs(bid - self.ticks[-1]['bid']) if self.ticks else 0
            self.ticks.append({'bid': bid, 'ask': ask, 'spread': spread, 'timestamp': timestamp, 'price_change': price_change})
            self.spread_samples.append(spread)
            if len(self.ticks) > 50:
                recent_changes = [t['price_change'] for t in self.ticks][-50:]
                mean_change, std_change = np.mean(recent_changes), np.std(recent_changes)
                if std_change > 1e-9 and price_change > mean_change + (DYNAMIC_THRESHOLD_STD_FACTOR * std_change):
                    self.potential_glitches.append(self.ticks[-1])
            return spread # بازگرداندن اسپرد جدید
        return self.current_spread # اگر تیک معتبر نبود، اسپرد قبلی را باز می‌گردانیم

    def add_simulated_slippage(self, order_type: str, request_price: float):
        if not self.ticks: return
        last_tick, slippage_pips = self.ticks[-1], 0
        if order_type == "BUY": slippage_pips = (last_tick['ask'] - request_price) * 100000
        elif order_type == "SELL": slippage_pips = (request_price - last_tick['bid']) * 100000
        self.slippage_samples.append({'type': order_type, 'slippage_pips': slippage_pips})

    def apply_penalty_decay(self):
        now = time.time()
        elapsed = now - self.last_penalty_decay_time
        if elapsed >= PENALTY_DECAY_INTERVAL:
            cycles = math.floor(elapsed / PENALTY_DECAY_INTERVAL)
            self.penalty_score *= (PENALTY_DECAY_RATE ** cycles)
            if self.penalty_score < 1e-5: self.penalty_score = 0.0
            self.last_penalty_decay_time = now

    def add_verified_glitch(self, glitch: Dict[str, Any], severity: float):
        glitch['severity'] = severity
        glitch['time_str'] = time.strftime('%H:%M:%S', time.localtime(glitch['timestamp']))
        self.verified_glitches.appendleft(glitch)
        self.penalty_score = min(100, self.penalty_score + severity)

    def add_latency_sample(self, latency_ms: float):
        self.latency_samples.append(latency_ms)

def get_all_brokers_by_symbol() -> Dict[str, List[BrokerState]]:
    return {symbol: list(brokers.values()) for symbol, brokers in instrument_states.items()}
def set_latest_analysis_results(results: Dict):
    global latest_analysis_results
    latest_analysis_results = results
def get_latest_analysis_results() -> Dict:
    return latest_analysis_results

async def handle_tick_request(request: Request):
    """
    Handles incoming ticks and returns tick data for real-time updates.
    """
    try:
        body = await request.body(); message = body.decode('utf-8')
        parts = message.split(',');
        if len(parts) == 5:
            broker, raw_symbol, _, bid_str, ask_str = parts
            bid, ask = float(sanitize_price_string(bid_str)), float(sanitize_price_string(ask_str))
            symbol = normalize_symbol(raw_symbol)
            if symbol not in instrument_states: instrument_states[symbol] = {}
            if broker not in instrument_states[symbol]: instrument_states[symbol][broker] = BrokerState(broker, symbol)

            current_spread = instrument_states[symbol][broker].add_tick(bid, ask, time.time())
            
            # بازگرداندن داده‌های تیک برای ارسال آنی
            return {
                "status": "success",
                "tick_data": {
                    "symbol": symbol,
                    "broker": broker,
                    "current_spread": current_spread
                }
            }
        return {"status": "invalid_format"}
    except Exception as e: return {"status": "error", "detail": str(e)}

async def handle_slippage_request(request: Request):
    try:
        body = await request.body(); message = body.decode('utf-8')
        parts = message.split(',');
        if len(parts) == 6:
            broker, raw_symbol, _, order_type, price_str, _ = parts
            price = float(sanitize_price_string(price_str)); symbol = normalize_symbol(raw_symbol)
            if symbol in instrument_states and broker in instrument_states[symbol]:
                instrument_states[symbol][broker].add_simulated_slippage(order_type, price)
                return {"status": "slippage_test_received"}
    except Exception as e: return {"status": "error", "detail": str(e)}

async def handle_latency_request(request: Request):
    try:
        server_receipt_time_ms = time.time() * 1000
        body = await request.body(); message = body.decode('utf-8')
        parts = message.split(',');
        if len(parts) == 3:
            broker, raw_symbol, client_send_time_ms_str = parts
            latency_ms = server_receipt_time_ms - float(client_send_time_ms_str)
            symbol = normalize_symbol(raw_symbol)
            if symbol in instrument_states and broker in instrument_states[symbol] and 0 < latency_ms < 5000:
                instrument_states[symbol][broker].add_latency_sample(latency_ms)
                return {"status": "latency_sample_received"}
        return {"status": "invalid_format"}
    except Exception as e: return {"status": "error", "detail": str(e)}