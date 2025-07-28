# analysis_engine.py
# v12.0: Added advanced spread and quote freeze analysis.

from typing import List, Dict
import numpy as np
import pandas as pd
from scipy.stats import shapiro
import time

from state_manager import BrokerState
from config import (
    FEED_FREEZE_THRESHOLD, LEADER_FOLLOWER_WINDOW_MS, GLITCH_VERIFICATION_THRESHOLD_PIPS,
    QUOTE_FREEZE_TICKS_WINDOW, QUOTE_FREEZE_UNIQUENESS_RATIO
)

def analyze_glitches_and_correlation(brokers: List[BrokerState]):
    """Analyzes glitches, correlation, and sets the leader flag."""
    active_brokers = [b for b in brokers if not is_broker_frozen(b)]
    for b in brokers: b.is_leader = False # Reset leader status

    if len(active_brokers) < 2:
        for b in active_brokers: b.correlation_with_leader = 0.5
        return

    leader = max(active_brokers, key=lambda b: len(b.ticks))
    leader.is_leader = True # Set leader flag
    leader_prices = pd.Series([t['bid'] for t in leader.ticks], index=[t['timestamp'] for t in leader.ticks])
    if leader_prices.empty: return

    for follower in active_brokers:
        if follower == leader:
            follower.correlation_with_leader = 1.0
            continue
        
        follower_prices = pd.Series([t['bid'] for t in follower.ticks], index=[t['timestamp'] for t in follower.ticks])
        if follower_prices.empty:
            follower.correlation_with_leader = 0.0
            continue
        
        combined = pd.concat([leader_prices, follower_prices], axis=1).ffill().bfill()
        if combined.shape[0] < 10 or combined.iloc[:, 0].equals(combined.iloc[:, 1]):
             follower.correlation_with_leader = 1.0
             continue
        
        correlation = combined.iloc[:, 0].corr(combined.iloc[:, 1])
        follower.correlation_with_leader = correlation if not np.isnan(correlation) else 0.0

        glitches_to_verify = follower.potential_glitches
        follower.potential_glitches = []
        for glitch in glitches_to_verify:
            leader_ticks_window = [t for t in leader.ticks if abs(t['timestamp'] - glitch['timestamp']) * 1000 <= LEADER_FOLLOWER_WINDOW_MS]
            if not leader_ticks_window: continue
            
            avg_leader_price = np.mean([t['bid'] for t in leader_ticks_window])
            deviation_pips = abs(glitch['bid'] - avg_leader_price) * 100000
            
            if deviation_pips > GLITCH_VERIFICATION_THRESHOLD_PIPS:
                severity = min(deviation_pips / 5, 25)
                follower.add_verified_glitch(glitch, severity)

def get_base_kpis(state: BrokerState) -> Dict:
    """Calculates basic KPIs like TPS, feed stability, and latency."""
    now = time.time()
    seconds_since_last_tick = now - state.last_update_time
    is_frozen = seconds_since_last_tick > FEED_FREEZE_THRESHOLD
    feed_stability_score = max(0, 100 - (seconds_since_last_tick * 5))
    ticks_in_last_sec = len([t for t in state.ticks if t['timestamp'] > now - 1])
    avg_latency_ms = np.mean(state.latency_samples) if state.latency_samples else 0

    return {
        "feed_stability_score": feed_stability_score,
        "is_frozen": is_frozen,
        "tps": ticks_in_last_sec,
        "avg_latency_ms": avg_latency_ms
    }

def get_advanced_spread_kpis(state: BrokerState) -> Dict:
    """Calculates advanced spread KPIs."""
    if not state.spread_samples:
        return {"avg_spread": 0, "spread_std_dev": 0, "max_spread": 0}
    
    spreads = list(state.spread_samples)
    return {
        "avg_spread": np.mean(spreads),
        "spread_std_dev": np.std(spreads),
        "max_spread": np.max(spreads)
    }

def get_quote_freeze_kpi(state: BrokerState) -> Dict:
    """Calculates a KPI for quote freezing."""
    ticks_to_check = list(state.ticks)[-QUOTE_FREEZE_TICKS_WINDOW:]
    if len(ticks_to_check) < QUOTE_FREEZE_TICKS_WINDOW / 2:
        return {"uniqueness_ratio": 1.0} # Not enough data, assume OK

    unique_prices = len(set(t['bid'] for t in ticks_to_check))
    uniqueness_ratio = unique_prices / len(ticks_to_check)
    return {"uniqueness_ratio": uniqueness_ratio}

def get_authenticity_kpis(state: BrokerState) -> Dict:
    normality_p_value = 0.5
    if len(state.tick_intervals) >= 50:
        try:
            _, p_val = shapiro(list(state.tick_intervals))
            normality_p_value = p_val if not np.isnan(p_val) else 0.0
        except:
            normality_p_value = 0.0

    return {
        "tick_distribution_p_value": normality_p_value,
        "correlation_with_leader": state.correlation_with_leader
    }

def get_execution_kpis(state: BrokerState) -> Dict:
    asymmetric_slippage_ratio = 1.0
    if len(state.slippage_samples) > 10:
        all_slippages = [s['slippage_pips'] for s in state.slippage_samples]
        positive_client_slippage = [s for s in all_slippages if s < -1e-9]
        negative_client_slippage = [s for s in all_slippages if s > 1e-9]
        avg_positive_client = abs(np.mean(positive_client_slippage)) if positive_client_slippage else 0
        avg_negative_client = abs(np.mean(negative_client_slippage)) if negative_client_slippage else 0
        
        if avg_positive_client > 1e-9:
            asymmetric_slippage_ratio = avg_negative_client / avg_positive_client
        elif avg_negative_client > 1e-9:
            asymmetric_slippage_ratio = 100.0
            
    return {"asymmetric_slippage_ratio": asymmetric_slippage_ratio}

def is_broker_frozen(state: BrokerState) -> bool:
    return (time.time() - state.last_update_time) > FEED_FREEZE_THRESHOLD
