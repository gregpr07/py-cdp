import asyncio
import json
from typing import Dict, Optional

import websockets


class CDPClient:
    def __init__(self, url: str):
        self.url = url
        self.ws: Optional[websockets.ClientConnection] = None
        self.msg_id: int = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}
        self._message_handler_task = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self):
        """Start the WebSocket connection and message handler task"""
        if self.ws is not None:
            raise RuntimeError("Client is already started")

        self.ws = await websockets.connect(self.url)
        self._message_handler_task = asyncio.create_task(self._handle_messages())

    async def stop(self):
        """Stop the message handler and close the WebSocket connection"""
        # Cancel the message handler task
        if self._message_handler_task:
            self._message_handler_task.cancel()
            try:
                await self._message_handler_task
            except asyncio.CancelledError:
                pass
            self._message_handler_task = None

        # Cancel all pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.set_exception(ConnectionError("Client is stopping"))
        self.pending_requests.clear()

        # Close the websocket connection
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def _handle_messages(self):
        """Continuously handle incoming messages"""
        try:
            while True:
                if not self.ws:
                    break

                raw = await self.ws.recv()
                data = json.loads(raw)

                if "id" in data and data["id"] in self.pending_requests:
                    future = self.pending_requests.pop(data["id"])
                    if "error" in data:
                        future.set_exception(RuntimeError(data["error"]))
                    else:
                        future.set_result(data["result"])
        except websockets.exceptions.ConnectionClosed:
            # Connection closed, resolve all pending futures with an exception
            for future in self.pending_requests.values():
                if not future.done():
                    future.set_exception(ConnectionError("WebSocket connection closed"))
            self.pending_requests.clear()
        except Exception as e:
            # Handle other exceptions
            for future in self.pending_requests.values():
                if not future.done():
                    future.set_exception(e)
            self.pending_requests.clear()

    async def send(
        self, method: str, params: dict | None = None, session_id: str | None = None
    ) -> dict:
        if not self.ws:
            raise RuntimeError(
                "Client is not started. Call start() first or use as async context manager."
            )

        self.msg_id += 1
        msg = {
            "id": int(self.msg_id),
            "method": method,
            "params": params or {},
        }

        if session_id:
            msg["sessionId"] = session_id

        # Create a future for this request
        future = asyncio.Future()
        self.pending_requests[self.msg_id] = future

        await self.ws.send(json.dumps(msg))

        # Wait for the response
        return await future
