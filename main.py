# main.py
# v11.1: The WebSocket Resilience Release
# This version fixes the RuntimeError when broadcasting to a closed connection.

import uvicorn
from fastapi import FastAPI, Request , WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
import asyncio
import time
import json
from typing import Set

# --- ماژول‌های پروژه ---
import state_manager
import analysis_engine
import scoring_engine
from config import (
    HOST, PORT, ANALYSIS_INTERVAL, FEED_FREEZE_THRESHOLD
)

# --- WebSocket Connection Manager (اصلاح‌شده) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"✅ کلاینت متصل شد. تعداد کل: {len(self.active_connections)}")


    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ کلاینت قطع شد. تعداد باقی‌مانده: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """
        پیام را به تمام اتصالات فعال ارسال می‌کند و اتصالات بسته‌شده را حذف می‌کند.
        """
        dead_connections: Set[WebSocket] = set()
        # ما روی یک کپی از set تکرار می‌کنیم تا بتوانیم در حین تکرار، نسخه اصلی را تغییر دهیم
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except RuntimeError:
                # این خطا زمانی رخ می‌دهد که اتصال قبلاً بسته شده باشد
                dead_connections.add(connection)
        
        # اتصالات مرده را از لیست اصلی حذف می‌کنیم
        for connection in dead_connections:
            self.disconnect(connection)

    async def broadcast_json(self, data: dict):
        """
        یک دیکشنری را به صورت JSON به تمام کلاینت‌ها ارسال می‌کند.
        """
        await self.broadcast(json.dumps(data))


manager = ConnectionManager()

# --- FastAPI Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("🚀 Starting Griffin Engine v11.1 (WebSocket Resilience)...")
    analysis_task = asyncio.create_task(analysis_loop())
    yield
    print("🛑 Stopping background tasks...")
    analysis_task.cancel()
    try:
        await analysis_task
    except asyncio.CancelledError:
        logging.info("Analysis loop successfully cancelled.")


app = FastAPI(title="Griffin Engine v11.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Core Analysis Loop ---
async def analysis_loop():
    while True:
        try:
            await asyncio.sleep(ANALYSIS_INTERVAL)
            
            all_brokers_by_symbol = state_manager.get_all_brokers_by_symbol()

            for symbol, brokers in all_brokers_by_symbol.items():
                analysis_engine.analyze_glitches_and_correlation(brokers)
                for broker_state in brokers:
                    broker_state.apply_penalty_decay()

            final_results = scoring_engine.calculate_final_scores(all_brokers_by_symbol)
            
            for symbol, broker_states_list in all_brokers_by_symbol.items():
                for broker_state in broker_states_list:
                    broker_name = broker_state.broker_name
                    current_spread_value = getattr(broker_state, 'current_spread', 0.0)
                    
                    if symbol in final_results and broker_name in final_results[symbol]:
                        final_results[symbol][broker_name]['current_spread'] = current_spread_value

            state_manager.set_latest_analysis_results(final_results)

            # ارسال تحلیل کامل به صورت دوره‌ای
            await manager.broadcast_json({
                "type": "full_analysis",
                "payload": final_results
            })

        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"FATAL ERROR in analysis_loop: {e}", exc_info=True)


# --- API Endpoints ---
@app.post("/tick")
async def receive_tick(request: Request):
    response = await state_manager.handle_tick_request(request)
    if response and response.get("status") == "success":
        tick_data = response.get("tick_data")
        if tick_data:
            await manager.broadcast_json({
                "type": "spread_update",
                **tick_data
            })
    return response

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
    await manager.connect(websocket)
    try:
        # ارسال وضعیت اولیه کامل هنگام اتصال
        initial_data = state_manager.get_latest_analysis_results()
        await websocket.send_json({
            "type": "full_analysis",
            "payload": initial_data
        })
        # اتصال را برای دریافت آپدیت‌ها باز نگه می‌داریم
        while True:
            # منتظر پیام از کلاینت (در صورت نیاز)
            await websocket.receive_text()
    except WebSocketDisconnect:
        # این یک رویداد طبیعی است و توسط disconnect مدیریت می‌شود
        pass
    except Exception as e:
        print(f"خطای غیرمنتظره در WebSocket رخ داد: {e}")
    finally:
        manager.disconnect(websocket)


def start_server():
    print("--- Griffin Engine v11.1 is ready to detect the truth ---")
    uvicorn.run("main:app", host=HOST, port=PORT, log_level="info", reload=True)

if __name__ == "__main__":
    start_server()