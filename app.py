import asyncio
import json

import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://crypto-price-websocket-beige.vercel.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_price = {}
MAX_CONNECTIONS = 3
price_queue = asyncio.Queue()

BINANCE_WS_URL = "wss://data-stream.binance.vision/stream?streams=btcusdt@ticker/ethusdt@ticker/bnbusdt@ticker"

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    def connection_count(self):
        return len(self.active_connections)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Client disconnected. Active clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected_clients = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_clients.append(connection)

        for connection in disconnected_clients:
            self.disconnect(connection)


manager = ConnectionManager()


@app.get("/")
def home():
    return {"message": "Server is running"}


@app.get("/price")
def get_price():
    return latest_price


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if manager.connection_count() >= MAX_CONNECTIONS:
        await websocket.accept()
        await websocket.send_json({
            "error": "Connection limit reached",
            "max_connections": MAX_CONNECTIONS
        })
        await websocket.close()
        return

    await manager.connect(websocket)

    try:
        while True:
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


async def listen_binance():
    global latest_price

    async with websockets.connect(BINANCE_WS_URL) as websocket:
        print("Connected to Binance combined WebSocket")

        while True:
            message = await websocket.recv()
            data = json.loads(message)

            payload = data["data"]

            price_data = {
                "symbol": payload["s"],
                "last_price": payload["c"],
                "price_change_percent": payload["P"],
                "timestamp": payload["E"],
            }

            latest_price = price_data

            print("Queued:", price_data)
            await price_queue.put(price_data)


async def process_price_queue():
    while True:
        price_data = await price_queue.get()

        print("Sending from queue:", price_data)
        await manager.broadcast(price_data)

        price_queue.task_done()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(listen_binance())
    asyncio.create_task(process_price_queue())