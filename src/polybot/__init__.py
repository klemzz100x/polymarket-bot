"""Polymarket trading infrastructure package."""

import asyncio
import sys

# On Windows, the default ProactorEventLoop raises a harmless RuntimeError on
# shutdown when transports are garbage-collected after the loop closes.
# The SelectorEventLoop avoids this without affecting any functionality.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

__all__ = ["__version__"]

__version__ = "0.1.0"

