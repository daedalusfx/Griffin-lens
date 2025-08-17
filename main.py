# main.py
# v11.0: The Functional Refactoring Release
# This version refactors the project into a modular, functional architecture.

import uvicorn
from fastapi import FastAPI, Request , WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
import asyncio
import time
import json

# --- ماژول‌های جدید پروژه ---
import state_manager
import analysis_engine
import scoring_engine
from config import (
    HOST, PORT, ANALYSIS_INTERVAL, FEED_FREEZE_THRESHOLD
)

# --- FastAPI Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("🚀 Starting Griffin Engine v11.0 (Modular & Functional)...")
    analysis_task = asyncio.create_task(analysis_loop())
    yield
    print("🛑 Stopping background tasks...")
    analysis_task.cancel()
    await asyncio.gather(analysis_task, return_exceptions=True)

app = FastAPI(title="Griffin Engine v11.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Core Analysis Loop (Now an Orchestrator) ---
async def analysis_loop():
    """
    The main loop now orchestrates the analysis by calling modular functions.
    """
    while True:
        try:
            await asyncio.sleep(ANALYSIS_INTERVAL)
            
            # 1. Get all active brokers grouped by symbol
            all_brokers_by_symbol = state_manager.get_all_brokers_by_symbol()

            # 2. Run analyses for each symbol
            for symbol, brokers in all_brokers_by_symbol.items():
                
                # Run analyses that require cross-broker data (leader/follower)
                analysis_engine.analyze_glitches_and_correlation(brokers)
                
                # Apply penalty decay for all brokers of the symbol
                for broker_state in brokers:
                    broker_state.apply_penalty_decay()

            # 3. Calculate final scores and update the global results
            final_results = scoring_engine.calculate_final_scores(all_brokers_by_symbol)
            state_manager.set_latest_analysis_results(final_results)

        except Exception as e:
            logging.error(f"FATAL ERROR in analysis_loop: {e}", exc_info=True)

# --- API Endpoints (They now interact with the state_manager) ---
@app.post("/tick")
async def receive_tick(request: Request):
    return await state_manager.handle_tick_request(request)

@app.post("/slippage_test")
async def receive_slippage_test(request: Request):
    return await state_manager.handle_slippage_request(request)

@app.post("/latency_test")
async def receive_latency_test(request: Request):
    return await state_manager.handle_latency_request(request)

@app.get("/api/live_analysis")
async def get_live_analysis():
    return state_manager.get_latest_analysis_results()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    این نقطه پایانی یک اتصال WebSocket را مدیریت می‌کند و به صورت مداوم
    آخرین نتایج تحلیل را برای کلاینت ارسال می‌کند.
    """
    await websocket.accept()
    print("✅ یک کلاینت به WebSocket متصل شد.")
    try:
        while True:
            # منتظر بمان تا دور بعدی تحلیل کامل شود
            await asyncio.sleep(ANALYSIS_INTERVAL)

            # اگر اتصال هنوز باز است، داده‌ها را بفرست
            if websocket.client_state == WebSocketState.CONNECTED:
                results = state_manager.get_latest_analysis_results()
                await websocket.send_json(results)

    except WebSocketDisconnect:
        print("❌ کلاینت از WebSocket قطع شد.")
    except Exception as e:
        print(f"خطایی در WebSocket رخ داد: {e}")
    finally:
        # در صورت قطع شدن، منابع را تمیز می‌کنیم
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
        print("اتصال WebSocket بسته شد.")

def start_server():
    print("--- Griffin Engine v11.0 is ready to detect the truth ---")
    uvicorn.run("main:app", host=HOST, port=PORT, log_level="info", reload=True)

if __name__ == "__main__":
    start_server()
