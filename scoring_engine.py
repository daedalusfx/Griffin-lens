# scoring_engine.py
# v13.0: Added timeframe average score calculation.

from typing import List, Dict, Deque
import numpy as np
import time

from state_manager import BrokerState
import analysis_engine
from config import WEIGHTS, QUOTE_FREEZE_UNIQUENESS_RATIO

# --- New in v13 ---
def calculate_timeframe_averages(history: Deque[tuple[float, float]]) -> Dict[str, float]:
    """Calculates the average score over different historical timeframes."""
    now = time.time()
    timeframes = {
        "15m": 15 * 60,
        "30m": 30 * 60,
        "1h": 60 * 60,
        "4h": 4 * 60 * 60,
        "8h": 8 * 60 * 60,
    }
    results = { "15m": 0.0, "30m": 0.0, "1h": 0.0, "4h": 0.0, "8h": 0.0 }
    
    if not history:
        return results

    # To optimize, we can iterate from the end of the list
    for tf_name, tf_seconds in timeframes.items():
        relevant_scores = [score for ts, score in history if now - ts <= tf_seconds]
        if relevant_scores:
            results[tf_name] = np.mean(relevant_scores) # type: ignore
            
    return results
# --- End New ---

def calculate_final_scores(all_brokers_by_symbol: Dict[str, List[BrokerState]]) -> Dict:
    final_results = {}
    for symbol, brokers_list in all_brokers_by_symbol.items():
        # ... (Step 1 and 2 for gathering and normalizing KPIs remain the same) ...
        symbol_results = {}
        active_kpis_list = []
        for state in brokers_list:
            base_kpis = analysis_engine.get_base_kpis(state)
            auth_kpis = analysis_engine.get_authenticity_kpis(state)
            exec_kpis = analysis_engine.get_execution_kpis(state)
            spread_kpis = analysis_engine.get_advanced_spread_kpis(state)
            freeze_kpis = analysis_engine.get_quote_freeze_kpi(state)
            kpis = {"broker_name": state.broker_name, "is_leader": state.is_leader, "data_integrity_score": 100.0 - state.penalty_score, "verified_glitches_log": list(state.verified_glitches)[:5], **base_kpis, **auth_kpis, **exec_kpis, **spread_kpis, **freeze_kpis}
            symbol_results[state.broker_name] = kpis
            if not kpis['is_frozen']: active_kpis_list.append(kpis)
        if active_kpis_list:
            best_spread = min((k['avg_spread'] for k in active_kpis_list if k['avg_spread'] > 0), default=1)
            min_std_dev = min((k['spread_std_dev'] for k in active_kpis_list if k['spread_std_dev'] > 0), default=1)
            for name, kpis in symbol_results.items():
                kpis['score_spread_level'] = (best_spread / kpis['avg_spread']) * 100 if kpis['avg_spread'] > 0 else 0
                kpis['score_spread_stability'] = (min_std_dev / kpis['spread_std_dev']) * 100 if kpis['spread_std_dev'] > 0 else 0
        else:
             for name, kpis in symbol_results.items():
                kpis['score_spread_level'] = 0
                kpis['score_spread_stability'] = 0

        # Step 3: Calculate final weighted score and all sub-scores
        for name, kpis in symbol_results.items():
            state = next((s for s in brokers_list if s.broker_name == name), None)
            if not state: continue

            # ... (Calculation of individual scores remains the same) ...
            score_authenticity = (max(0, (kpis['correlation_with_leader'] - 0.95) / 0.05) * 50 if kpis['correlation_with_leader'] > 0.95 else 0) + (kpis['tick_distribution_p_value'] * 50)
            score_integrity = kpis['data_integrity_score']
            score_execution = (1 - min(abs(1 - kpis['asymmetric_slippage_ratio']), 2) / 2) * 100
            score_feed_stability = kpis['feed_stability_score']
            score_tps = min((kpis['tps'] / 25) * 100, 100)
            score_quote_freeze = 100 if kpis['uniqueness_ratio'] > QUOTE_FREEZE_UNIQUENESS_RATIO else 0
            
            final_score = (score_authenticity * WEIGHTS['authenticity'] + score_integrity * WEIGHTS['integrity'] + score_execution * WEIGHTS['execution'] + kpis.get('score_spread_level', 0) * WEIGHTS['spread_level'] + kpis.get('score_spread_stability', 0) * WEIGHTS['spread_stability'] + score_feed_stability * WEIGHTS['feed_stability'] + score_quote_freeze * WEIGHTS['quote_freeze'] + score_tps * WEIGHTS['tps'])
            
            kpis['quality_score'] = max(0, min(100, final_score))
            # ... (Adding sub-scores to kpis dict remains the same) ...
            kpis['score_authenticity'] = score_authenticity
            kpis['score_integrity'] = score_integrity
            kpis['score_execution'] = score_execution
            kpis['score_feed_stability'] = score_feed_stability
            kpis['score_quote_freeze'] = score_quote_freeze
            kpis['score_tps'] = score_tps

            # --- Changed in v13 ---
            # Add current score to history
            state.add_score_to_history(kpis['quality_score'], time.time())
            
            # Add timeframe averages and short history for sparkline to the response
            kpis['timeframe_averages'] = calculate_timeframe_averages(state.quality_score_history)
            kpis['score_history'] = [s for ts, s in list(state.quality_score_history)[-30:]] # last 30 for sparkline
            # --- End Change ---

        final_results[symbol] = symbol_results
        
    return final_results
