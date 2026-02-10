from typing import Any

from fastapi import APIRouter, Depends

from app.deps_auth import get_current_user

router = APIRouter()


@router.get("/me")
async def me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    return {
        "id": str(user["id"]),
        "email": str(user.get("email", "")),
    }
