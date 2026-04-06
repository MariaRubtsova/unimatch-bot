from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert as pg_insert

from api.auth import verify_telegram_init_data, create_jwt
from db.database import AsyncSessionLocal
from db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class InitDataRequest(BaseModel):
    init_data: str


class TokenResponse(BaseModel):
    token: str
    user_id: int
    first_name: str


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(body: InitDataRequest):
    import logging
    logger = logging.getLogger(__name__)
    print(f"AUTH: init_data length={len(body.init_data)}", flush=True)

    if not body.init_data:
        print("AUTH: empty init_data, returning Dev", flush=True)
        return TokenResponse(token=create_jwt(0), user_id=0, first_name="Dev")

    user_data = verify_telegram_init_data(body.init_data)
    user_id = int(user_data["id"])
    first_name = user_data.get("first_name", "")
    username = user_data.get("username")
    print(f"AUTH: user_id={user_id}, first_name={first_name}", flush=True)

    async with AsyncSessionLocal() as session:
        stmt = pg_insert(User).values(
            user_id=user_id,
            username=username,
            first_name=first_name,
        ).on_conflict_do_update(
            index_elements=["user_id"],
            set_={"last_active": User.last_active, "username": username, "first_name": first_name},
        )
        await session.execute(stmt)
        await session.commit()

    token = create_jwt(user_id)
    return TokenResponse(token=token, user_id=user_id, first_name=first_name)
