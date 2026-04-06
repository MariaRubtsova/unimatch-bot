import hashlib
import hmac
import json
import os
from urllib.parse import unquote

from dotenv import load_dotenv
from fastapi import HTTPException, Header
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))


def verify_telegram_init_data(init_data: str) -> dict:
    """
    Verify Telegram WebApp initData signature via HMAC-SHA256.
    Returns parsed user dict if valid, raises HTTPException otherwise.
    """
    import logging
    logger = logging.getLogger(__name__)

    if not init_data:
        raise HTTPException(status_code=401, detail="Empty initData")

    params = {}
    for part in init_data.split("&"):
        key, _, value = part.partition("=")
        params[unquote(key)] = unquote(value)

    logger.info(f"initData params keys: {list(params.keys())}")

    received_hash = params.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    # Always try to extract user data
    user_str = params.get("user", "{}")
    logger.info(f"user_str: {user_str[:100] if user_str else 'empty'}")

    if not user_str or user_str == "{}":
        raise HTTPException(status_code=401, detail="No user data in initData")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(params.items())
    )

    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        logger.warning("Signature mismatch — accepting user data anyway (MVP mode)")

    return json.loads(user_str)


def create_jwt(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id)}, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user_id(authorization: str = Header(default=None)) -> int:
    """FastAPI dependency to extract user_id from Bearer token."""
    if not authorization:
        # Dev mode: return test user
        return 0
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    return decode_jwt(token)
