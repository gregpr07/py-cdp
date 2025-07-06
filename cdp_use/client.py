import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

import websockets

if TYPE_CHECKING:
    from cdp_use.cdp.library import CDPLibrary

# Set up logging
logger = logging.getLogger(__name__)


class CDPClient:
    def __init__(self, url: str):
        self.url = url
        self.ws: Optional[websockets.ClientConnection] = None
        self.msg_id: int = 0
        self.pending_requests: Dict[int, asyncio.Future] = {}
        self._message_handler_task = None
        # self.event_handlers: Dict[str, Callable] = {}

        # Initialize the type-safe CDP library
        from cdp_use.cdp.library import CDPLibrary

        self.send: "CDPLibrary" = CDPLibrary(self)

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    # def on_event(self, method: str, handler: Callable):
    #     """Register an event handler for CDP events"""
    #     self.event_handlers[method] = handler

    async def start(self):
        """Start the WebSocket connection and message handler task"""
        if self.ws is not None:
            raise RuntimeError("Client is already started")

        logger.info(f"Connecting to {self.url}")
        self.ws = await websockets.connect(
            self.url,
            max_size=100 * 1024 * 1024,  # 100MB limit instead of default 1MB
        )
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

                # Handle response messages (with id)
                if "id" in data and data["id"] in self.pending_requests:
                    future = self.pending_requests.pop(data["id"])
                    if "error" in data:
                        logger.error(
                            f"CDP Error for request {data['id']}: {data['error']}"
                        )
                        future.set_exception(RuntimeError(data["error"]))
                    else:
                        future.set_result(data["result"])

                # Handle event messages (without id, but with method)
                elif "method" in data:
                    method = data["method"]
                    data.get("params", {})
                    session_id = data.get("sessionId")

                    logger.debug(f"Received event: {method} (session: {session_id})")

                    # TODO: find a nice way to register type safe event handlers (IGNORE this for now)
                    # # Call registered event handler if available
                    # if method in self.event_handlers:
                    #     try:
                    #         self.event_handlers[method](params, session_id)
                    #     except Exception as e:
                    #         logger.error(f"Error in event handler for {method}: {e}")

                # Handle unexpected messages
                else:
                    logger.warning(f"Received unexpected message: {data}")

        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
            # Connection closed, resolve all pending futures with an exception
            for future in self.pending_requests.values():
                if not future.done():
                    future.set_exception(ConnectionError("WebSocket connection closed"))
            self.pending_requests.clear()
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            # Handle other exceptions
            for future in self.pending_requests.values():
                if not future.done():
                    future.set_exception(e)
            self.pending_requests.clear()

    async def send_raw(
        self,
        method: str,
        params: Optional[Any] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
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

        logger.debug(f"Sending: {method} (id: {self.msg_id}, session: {session_id})")
        await self.ws.send(json.dumps(msg))

        # Wait for the response
        return await future
