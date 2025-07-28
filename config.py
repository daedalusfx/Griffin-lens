# config.py
# v13.0: Added Timeframe Analysis
# Central configuration file for the Griffin Engine.

# --- Server Configuration ---
HOST = "127.0.0.1"
PORT = 5000
ANALYSIS_INTERVAL = 1.0  # seconds

# --- Core Analysis Thresholds ---
FEED_FREEZE_THRESHOLD = 10.0 # seconds
LEADER_FOLLOWER_WINDOW_MS = 750 # milliseconds
GLITCH_VERIFICATION_THRESHOLD_PIPS = 10.0
DYNAMIC_THRESHOLD_STD_FACTOR = 3.5
QUOTE_FREEZE_TICKS_WINDOW = 50 
QUOTE_FREEZE_UNIQUENESS_RATIO = 0.1

# --- Data Buffer Sizes ---
TICK_BUFFER_SIZE = 500
# New: Increased history size for timeframe analysis (8 hours * 3600 seconds)
MAX_SCORE_HISTORY_RECORDS = 8 * 3600 

# --- Algorithmic Scoring Configuration ---
PENALTY_DECAY_RATE = 0.995
PENALTY_DECAY_INTERVAL = 1.0

# --- Final Score Weights ---
WEIGHTS = {
    'authenticity': 0.30,
    'integrity': 0.25,
    'execution': 0.15,
    'spread_level': 0.05,
    'spread_stability': 0.05,
    'feed_stability': 0.10,
    'quote_freeze': 0.05,
    'tps': 0.05
}
