from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from polybot.core.config import Settings, get_settings


async def verify_automation_secret(
    x_automation_secret: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.polybot_automation_secret
    if expected and x_automation_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid automation secret",
        )

