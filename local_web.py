import os
import secrets
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from livekit import api


BASE_DIR = Path(__file__).resolve().parent
WEB_DIST = BASE_DIR / "web" / "dist"
load_dotenv(BASE_DIR / ".env")

app = FastAPI()


@app.post("/api/session")
def create_session() -> dict[str, str]:
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    if not livekit_url or not api_key or not api_secret:
        raise HTTPException(
            status_code=503,
            detail="Set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in .env.",
        )

    room_name = f"browser-{secrets.token_hex(8)}"
    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(f"guest-{secrets.token_hex(6)}")
        .with_name("Browser guest")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .with_room_config(
            api.RoomConfiguration(
                agents=[api.RoomAgentDispatch(agent_name="my-agent")]
            )
        )
        .to_jwt()
    )
    return {
        "server_url": livekit_url,
        "participant_token": token,
        "room_name": room_name,
    }


@app.get("/")
def index() -> FileResponse:
    index_file = WEB_DIST / "index.html"
    if not index_file.is_file():
        raise HTTPException(
            status_code=503,
            detail="Browser client is not built. Run npm.cmd --prefix web run build.",
        )
    return FileResponse(index_file)


if (WEB_DIST / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=WEB_DIST / "assets"),
        name="assets",
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)