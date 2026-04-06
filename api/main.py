import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from api.routes import match, deadlines, checklist, chat, export, auth_routes
from db.database import engine
from admin.views import setup_admin

app = FastAPI(title="UniMatch API", version="1.0.0")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "change_me"))
setup_admin(app, engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(match.router)
app.include_router(deadlines.router)
app.include_router(checklist.router)
app.include_router(chat.router)
app.include_router(export.router)

# Serve Mini App static files with no-cache headers
from fastapi.responses import FileResponse
from fastapi import Request

mini_app_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mini_app")

@app.get("/mini_app/index.html")
async def serve_mini_app(request: Request):
    return FileResponse(
        os.path.join(mini_app_path, "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )

app.mount("/mini_app", StaticFiles(directory=mini_app_path, html=True), name="mini_app")


@app.get("/health")
async def health():
    return {"status": "ok"}
