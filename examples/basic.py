import asyncio
from typing import Optional

from cdp_use.cdp.page.events import DomContentEventFiredEvent
from cdp_use.cdp.runtime.events import ConsoleAPICalledEvent
from cdp_use.cdp.target.events import AttachedToTargetEvent
from cdp_use.client import CDPClient


def on_attached_to_target(
    event: AttachedToTargetEvent, session_id: Optional[str]
) -> None:
    print(
        f"Attached to target: {event['targetInfo']['title']}, session_id: {session_id}"
    )


def on_dom_content_loaded(
    event: DomContentEventFiredEvent, session_id: Optional[str]
) -> None:
    print(f"DOM content loaded at: {event['timestamp']}, session_id: {session_id}")


def on_console_message(event: ConsoleAPICalledEvent, session_id: Optional[str]) -> None:
    print(f"Console: {event['type']}, session_id: {session_id}")


async def main():
    async with CDPClient("ws://127.0.0.1:9222/devtools/browser/...") as client:
        # Register event handlers with camelCase method names (matching CDP)
        client.register.Target.attachedToTarget(on_attached_to_target)
        client.register.Page.domContentEventFired(on_dom_content_loaded)
        client.register.Runtime.consoleAPICalled(on_console_message)

        targets = await client.send.Target.getTargets()
        print(targets)

        target_id = targets["targetInfos"][0]["targetId"]
        attach_to_target_response = await client.send.Target.attachToTarget(
            params={"targetId": target_id, "flatten": True}
        )

        session_id = attach_to_target_response["sessionId"]

        if session_id is None:
            raise ValueError("Session ID is None")

        # Enable domains to start receiving events
        # await client.send.Page.enable()
        # await client.send.Runtime.enable()

        # Navigate and receive events
        await client.send.Page.navigate(
            {"url": "https://example.com"}, session_id=session_id
        )
        await asyncio.sleep(20)  # Keep listening for events


if __name__ == "__main__":
    asyncio.run(main())
