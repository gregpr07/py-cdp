import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

import httpx

from cdp_use.client import CDPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TargetWatchdog:
    def __init__(self, cdp_client: CDPClient):
        self.cdp = cdp_client
        self.crashed_targets: Dict[str, datetime] = {}  # target_id -> crashed_at timestamp
        self.attached_sessions: Dict[str, str] = {}  # target_id -> session_id
        self.closed_targets: Set[str] = set()  # targets we should stop checking
        self.scan_interval = 10  # seconds
        self.reload_threshold = timedelta(seconds=60)
        self.close_threshold = timedelta(seconds=90)

    async def attach_to_target(self, target_id: str) -> Optional[str]:
        """Attach to a target and return the session ID."""
        try:
            result = await self.cdp.send.Target.attachToTarget(
                params={"targetId": target_id, "flatten": True}
            )
            session_id = result["sessionId"]
            self.attached_sessions[target_id] = session_id
            
            # Enable Runtime domain for JS evaluation
            await self.cdp.send.Runtime.enable(session_id=session_id)
            
            return session_id
        except Exception as e:
            logger.error(f"Failed to attach to target {target_id}: {e}")
            return None

    async def check_target_health(self, target_id: str, session_id: str) -> bool:
        """Check if a target is responsive by evaluating 1+1."""
        try:
            # Set a short timeout for the evaluation
            result = await asyncio.wait_for(
                self.cdp.send.Runtime.evaluate(
                    params={"expression": "1+1", "returnByValue": True},
                    session_id=session_id
                ),
                timeout=5.0  # 5 second timeout
            )
            
            # Check if the result is 2
            if result.get("result", {}).get("value") == 2:
                return True
            else:
                logger.warning(f"Target {target_id} returned unexpected result: {result}")
                return False
                
        except asyncio.TimeoutError:
            logger.warning(f"Target {target_id} timed out during health check")
            return False
        except Exception as e:
            logger.error(f"Health check failed for target {target_id}: {e}")
            return False

    async def reload_target(self, target_id: str, session_id: str):
        """Reload a crashed target."""
        try:
            await self.cdp.send.Page.reload(session_id=session_id)
            logger.info(f"Reloaded target {target_id}")
        except Exception as e:
            logger.error(f"Failed to reload target {target_id}: {e}")

    async def close_and_replace_target(self, target_id: str):
        """Close a target and create a new about:blank tab."""
        try:
            # Close the target
            await self.cdp.send.Target.closeTarget(params={"targetId": target_id})
            logger.info(f"Closed crashed target {target_id}")
            
            # Create a new about:blank tab
            result = await self.cdp.send.Target.createTarget(params={"url": "about:blank"})
            new_target_id = result["targetId"]
            logger.info(f"Created replacement target {new_target_id}")
            
            # Mark the old target as closed
            self.closed_targets.add(target_id)
            
        except Exception as e:
            logger.error(f"Failed to close and replace target {target_id}: {e}")

    async def scan_targets(self):
        """Scan all targets and check their health."""
        try:
            # Get all targets
            targets_result = await self.cdp.send.Target.getTargets()
            page_targets = [t for t in targets_result["targetInfos"] if t["type"] == "page"]
            
            current_time = datetime.now()
            
            for target in page_targets:
                target_id = target["targetId"]
                
                # Skip closed targets
                if target_id in self.closed_targets:
                    continue
                
                # Check if target was closed by user
                if target.get("attached") is False:
                    logger.info(f"Target {target_id} was closed, stopping monitoring")
                    self.closed_targets.add(target_id)
                    if target_id in self.crashed_targets:
                        del self.crashed_targets[target_id]
                    if target_id in self.attached_sessions:
                        del self.attached_sessions[target_id]
                    continue
                
                # Attach to target if not already attached
                if target_id not in self.attached_sessions:
                    session_id = await self.attach_to_target(target_id)
                    if not session_id:
                        continue
                else:
                    session_id = self.attached_sessions[target_id]
                
                # Check target health
                is_healthy = await self.check_target_health(target_id, session_id)
                
                if is_healthy:
                    # Target is responsive
                    if target_id in self.crashed_targets:
                        logger.info(f"Target {target_id} is now responsive, resetting crashed status")
                        del self.crashed_targets[target_id]
                else:
                    # Target is unresponsive
                    if target_id not in self.crashed_targets:
                        logger.warning(f"Target {target_id} is unresponsive, marking as crashed")
                        self.crashed_targets[target_id] = current_time
                    else:
                        # Check how long it's been crashed
                        crashed_duration = current_time - self.crashed_targets[target_id]
                        
                        if crashed_duration >= self.close_threshold:
                            # Close and replace after 90 seconds
                            logger.error(f"Target {target_id} crashed for {crashed_duration.seconds}s, closing and replacing")
                            await self.close_and_replace_target(target_id)
                            del self.crashed_targets[target_id]
                            if target_id in self.attached_sessions:
                                del self.attached_sessions[target_id]
                        elif crashed_duration >= self.reload_threshold:
                            # Reload after 60 seconds
                            logger.warning(f"Target {target_id} crashed for {crashed_duration.seconds}s, attempting reload")
                            await self.reload_target(target_id, session_id)
                            # Recheck health after reload
                            await asyncio.sleep(2)  # Give it time to reload
                            is_healthy_after_reload = await self.check_target_health(target_id, session_id)
                            if is_healthy_after_reload:
                                logger.info(f"Target {target_id} recovered after reload")
                                del self.crashed_targets[target_id]
                
        except Exception as e:
            logger.error(f"Error during target scan: {e}")

    async def run(self):
        """Run the watchdog service."""
        logger.info("Starting target watchdog service...")
        
        while True:
            await self.scan_targets()
            await asyncio.sleep(self.scan_interval)


async def main():
    # Get WebSocket URL
    async with httpx.AsyncClient() as client:
        version_info = await client.get("http://localhost:9222/json/version")
        browser_ws_url = version_info.json()["webSocketDebuggerUrl"]
    
    # Connect to Chrome DevTools
    async with CDPClient(browser_ws_url) as cdp:
        watchdog = TargetWatchdog(cdp)
        
        try:
            await watchdog.run()
        except KeyboardInterrupt:
            logger.info("Watchdog service stopped by user")


if __name__ == "__main__":
    asyncio.run(main())