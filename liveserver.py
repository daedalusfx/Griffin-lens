# backend/live_server.py
# v10.2: The NameError Bugfix Release
# Fixed a NameError by re-adding missing penalty decay configuration variables.

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio
import time
import re
from typing import Dict, List, Deque, Any
from collections import deque
import numpy as np
import pandas as pd
from scipy.stats import shapiro # For normality test on tick intervals
from contextlib import asynccontextmanager
import math

# --- Configuration ---
HOST = "127.0.0.1"
PORT = 5000
ANALYSIS_INTERVAL = 1.0
FEED_FREEZE_THRESHOLD = 10.0
# --- Config for Authenticity Analysis ---
CORRELATION_WINDOW = 100 # Use last 100 ticks for correlation
TICK_DISTRIBUTION_WINDOW = 150 # Use last 150 tick intervals for distribution test
GLITCH_VERIFICATION_THRESHOLD_PIPS = 10.0
LEADER_FOLLOWER_WINDOW_MS = 750
DYNAMIC_THRESHOLD_STD_FACTOR = 3.5

# --- Algorithmic Scoring Configuration ---
# --- FIX: Re-added missing configuration variables ---
PENALTY_DECAY_RATE = 0.995
PENALTY_DECAY_INTERVAL = 1.0

WEIGHTS = {
    'authenticity': 0.40, # اصالت داده (جدید و بسیار مهم)
    'integrity': 0.25,    # یکپارچگی داده (گلیچ)
    'execution': 0.20,    # کیفیت اجرا (لغزش)
    'spread': 0.05,       # هزینه اسپرد
    'stability': 0.05,    # پایداری فید
    'tps': 0.05           # تعداد تیک در ثانیه
}

# --- Utility Functions ---
def normalize_symbol(symbol: str) -> str:
    """استانداردسازی نام نماد معاملاتی."""
    match = re.match(r"([A-Z]{6})", symbol.upper())
    return match.group(1) if match else re.sub(r'[^A-Z0-9]', '', symbol.upper())

def sanitize_price_string(price_str: str) -> str:
    """هر کاراکتری به جز عدد و نقطه را از رشته حذف می‌کند."""
    if not price_str: return "0.0"
    return re.sub(r'[^\d.]', '', price_str)

# --- Broker State Manager ---
class BrokerState:
    def __init__(self, broker_name: str, symbol: str):
        self.broker_name = broker_name
        self.symbol = symbol
        self.last_update_time = time.time()
        self.ticks: Deque[Dict[str, Any]] = deque(maxlen=500)
        self.potential_glitches: List[Dict[str, Any]] = []
        self.penalty_score = 0.0
        self.last_penalty_decay_time = time.time()
        self.verified_glitches: Deque[Dict[str, Any]] = deque(maxlen=100)
        self.spread_history: Deque[float] = deque(maxlen=200)
        self.slippage_samples: Deque[Dict[str, float]] = deque(maxlen=200)
        self.latency_samples: Deque[float] = deque(maxlen=100)
        self.tick_intervals: Deque[float] = deque(maxlen=TICK_DISTRIBUTION_WINDOW)
        self.last_tick_time = None
        self.correlation_with_leader = 0.5 # Default neutral value

    def add_tick(self, bid: float, ask: float, timestamp: float):
        """
        FIXED: Separated liveness updates from data validation to prevent processing halt.
        """
        # Step 1: Always update liveness metrics regardless of tick validity
        self.last_update_time = timestamp
        if self.last_tick_time:
            self.tick_intervals.append(timestamp - self.last_tick_time)
        self.last_tick_time = timestamp

        # Step 2: Only process and store the tick if the spread is valid (ask > bid)
        if ask > bid:
            spread = (ask - bid) * 100000
            price_change = abs(bid - self.ticks[-1]['bid']) if self.ticks else 0
            self.ticks.append({'bid': bid, 'ask': ask, 'spread': spread, 'timestamp': timestamp, 'price_change': price_change})
            self.spread_history.append(spread)

            # Glitch detection logic
            if len(self.ticks) > 50:
                recent_price_changes = np.array([t['price_change'] for t in self.ticks])[-50:]
                mean_change, std_change = np.mean(recent_price_changes), np.std(recent_price_changes)
                if std_change > 1e-9 and price_change > mean_change + (DYNAMIC_THRESHOLD_STD_FACTOR * std_change):
                    self.potential_glitches.append(self.ticks[-1])

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
        self.verified_glitches.append(glitch)
        self.penalty_score += severity
        self.penalty_score = min(self.penalty_score, 100)

    def add_latency_sample(self, latency_ms: float):
        self.latency_samples.append(latency_ms)

    def get_authenticity_data(self) -> Dict[str, Any]:
        normality_p_value = 0.5
        if len(self.tick_intervals) >= 50:
            try:
                stat, p_val = shapiro(list(self.tick_intervals))
                normality_p_value = p_val if not np.isnan(p_val) else 0.0
            except: # Catch any potential errors from shapiro test
                normality_p_value = 0.0
        return {
            "tick_distribution_p_value": normality_p_value,
            "price_series": pd.Series([t['bid'] for t in self.ticks], index=[t['timestamp'] for t in self.ticks])
        }

    def get_kpis(self) -> Dict[str, Any]:
        now = time.time()
        data_integrity_score = 100.0 - self.penalty_score
        seconds_since_last_tick = now - self.last_update_time
        is_frozen = seconds_since_last_tick > FEED_FREEZE_THRESHOLD
        feed_stability_score = max(0, 100 - (seconds_since_last_tick * 5))
        avg_spread = np.mean(self.spread_history) if self.spread_history else 0
        ticks_per_sec = len([t for t in self.ticks if t['timestamp'] > now - 1])
        avg_latency = np.mean(self.latency_samples) if self.latency_samples else 0
        pos_avg, neg_avg, asymmetry_ratio = 0, 0, 1.0
        if self.slippage_samples:
            all_slips = [s['slippage_pips'] for s in self.slippage_samples]
            pos_slips = [s for s in all_slips if s > 0]; neg_slips = [s for s in all_slips if s < 0]
            pos_avg, neg_avg = np.mean(pos_slips) if pos_slips else 0, np.mean(neg_slips) if neg_slips else 0
            if pos_avg > 1e-9: asymmetry_ratio = abs(neg_avg / pos_avg)
            elif neg_avg < -1e-9: asymmetry_ratio = 100.0
        return {
            "data_integrity_score": data_integrity_score, "feed_stability_score": feed_stability_score,
            "avg_spread": avg_spread, "tps": ticks_per_sec, "avg_latency_ms": avg_latency,
            "asymmetric_slippage_ratio": asymmetry_ratio, "is_frozen": is_frozen,
        }

# --- Global State & FastAPI Setup ---
instrument_states: Dict[str, Dict[str, BrokerState]] = {}
latest_analysis_results = {}
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("🚀 Starting Griffin Engine v10.2 (NameError Bugfix)...")
    analysis_task = asyncio.create_task(analysis_loop())
    yield
    print("🛑 Stopping background tasks...")
    analysis_task.cancel()
    await asyncio.gather(analysis_task, return_exceptions=True)
app = FastAPI(title="Griffin Engine v10.2", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Core Logic Loop ---
async def analysis_loop():
    global latest_analysis_results
    while True:
        try:
            await asyncio.sleep(ANALYSIS_INTERVAL)
            all_brokers_by_symbol: Dict[str, List[BrokerState]] = {s: list(b.values()) for s, b in instrument_states.items()}

            for symbol, brokers in all_brokers_by_symbol.items():
                active_brokers = [b for b in brokers if not b.get_kpis()['is_frozen']]
                if len(active_brokers) < 2:
                    for b in active_brokers: b.correlation_with_leader = 0.5 # Reset if not comparable
                    continue
                
                leader = max(active_brokers, key=lambda b: b.get_kpis()['tps'])
                leader_auth_data = leader.get_authenticity_data()
                if leader_auth_data['price_series'].empty: continue
                
                for follower in active_brokers:
                    if follower == leader:
                        follower.correlation_with_leader = 1.0
                        continue
                    follower_auth_data = follower.get_authenticity_data()
                    if follower_auth_data['price_series'].empty: continue
                    
                    combined_prices = pd.concat([leader_auth_data['price_series'], follower_auth_data['price_series']], axis=1).ffill().bfill()
                    correlation = combined_prices.iloc[:, 0].corr(combined_prices.iloc[:, 1])
                    follower.correlation_with_leader = correlation if not np.isnan(correlation) else 0.0
            
            temp_results = {}
            for symbol, brokers_list in all_brokers_by_symbol.items():
                for state in brokers_list: state.apply_penalty_decay()
                symbol_results = {}
                for state in brokers_list:
                    kpis = state.get_kpis()
                    auth_data = state.get_authenticity_data()
                    
                    score_correlation = max(0, (state.correlation_with_leader - 0.95) / (1.0 - 0.95)) * 50 if state.correlation_with_leader > 0.95 else 0
                    score_distribution = auth_data['tick_distribution_p_value'] * 50
                    kpis['authenticity_score'] = score_correlation + score_distribution
                    
                    score_integrity = kpis['data_integrity_score']
                    score_stability = kpis['feed_stability_score']
                    score_tps = (kpis['tps'] / 25) * 100 if kpis['tps'] < 25 else 100
                    score_execution = (1 - min(abs(1 - kpis['asymmetric_slippage_ratio']), 2) / 2) * 100
                    
                    kpis['score_integrity_w'] = score_integrity * WEIGHTS['integrity']
                    kpis['score_execution_w'] = score_execution * WEIGHTS['execution']
                    kpis['score_stability_w'] = score_stability * WEIGHTS['stability']
                    kpis['score_tps_w'] = score_tps * WEIGHTS['tps']
                    kpis['authenticity_score_w'] = kpis['authenticity_score'] * WEIGHTS['authenticity']
                    
                    symbol_results[state.broker_name] = kpis

                if len(brokers_list) > 1:
                    best_spread = min((kpi['avg_spread'] for kpi in symbol_results.values() if kpi['avg_spread'] > 0), default=1)
                    for name, kpis in symbol_results.items():
                        score_spread = (best_spread / (kpis['avg_spread'] or 1)) * 100
                        kpis['score_spread_w'] = score_spread * WEIGHTS['spread']
                else:
                    for name, kpis in symbol_results.items(): kpis['score_spread_w'] = 50 * WEIGHTS['spread']

                for name, kpis in symbol_results.items():
                    final_score = (kpis['authenticity_score_w'] + kpis['score_integrity_w'] + kpis['score_execution_w'] + 
                                   kpis['score_spread_w'] + kpis['score_stability_w'] + kpis['score_tps_w'])
                    kpis['quality_score'] = max(0, min(100, final_score))

                temp_results[symbol] = symbol_results
            latest_analysis_results = temp_results
        except Exception as e:
            logging.error(f"FATAL ERROR in analysis_loop: {e}", exc_info=True)


# --- API Endpoints ---
@app.post("/tick")
async def receive_tick(request: Request):
    try:
        body = await request.body(); message = body.decode('utf-8')
        parts = message.split(',');
        if len(parts) == 5:
            broker, raw_symbol, _, bid_str, ask_str = parts
            bid, ask = float(sanitize_price_string(bid_str)), float(sanitize_price_string(ask_str))
            symbol = normalize_symbol(raw_symbol)
            if symbol not in instrument_states: instrument_states[symbol] = {}
            if broker not in instrument_states[symbol]: instrument_states[symbol][broker] = BrokerState(broker, symbol)
            instrument_states[symbol][broker].add_tick(bid, ask, time.time())
            return {"status": "success"}
    except Exception as e: return {"status": "error", "detail": str(e)}

@app.post("/slippage_test")
async def receive_slippage_test(request: Request):
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

@app.post("/latency_test")
async def receive_latency_test(request: Request):
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

@app.get("/api/live_analysis")
async def get_live_analysis():
    return latest_analysis_results

def start_server():
    print("--- Griffin Engine v10.2 (NameError Bugfix) ---")
    uvicorn.run("liveserver:app", host=HOST, port=PORT, log_level="info", reload=True)

if __name__ == "__main__":
    start_server()
