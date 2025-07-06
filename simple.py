import asyncio
import json
import logging

import httpx
import websockets

from src.client import CDPClient

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # Get WebSocket URL using async HTTPX
    async with httpx.AsyncClient() as client:
        version_info = await client.get("http://localhost:9222/json/version")
        browser_ws_url = version_info.json()["webSocketDebuggerUrl"]
    # browser_ws_url = "ws://localhost:3000"

    # Connect to browser WebSocket
    async with CDPClient(browser_ws_url) as cdp:
        cdp: CDPClient
        # List all targets (tabs, extensions, etc.)
        targets_result = await cdp.send("Target.getTargets")
        page_targets = [t for t in targets_result["targetInfos"] if t["type"] == "page"]
        if not page_targets:
            raise RuntimeError("No page targets found.")

        target_id = page_targets[0]["targetId"]

        print(target_id, targets_result)

        # Attach to selected tab
        attach_result = await cdp.send(
            "Target.attachToTarget", {"targetId": target_id, "flatten": True}
        )
        session_id = attach_result["sessionId"]

        # Enable DOM domain
        await cdp.send("DOM.enable", session_id=session_id)

        # Get full DOM tree
        dom_result = await cdp.send(
            "DOM.getDocument", {"depth": -1, "pierce": True}, session_id=session_id
        )

        print("Root node ID:", dom_result["root"]["nodeId"])

        # spam 10 concurrent requests
        tasks = [
            cdp.send(
                "DOM.getDocument", {"depth": -1, "pierce": True}, session_id=session_id
            )
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)
        print(len(results))

        # print(results[-1])


asyncio.run(main())
