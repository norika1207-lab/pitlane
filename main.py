import sys
sys.path.insert(0, "/opt/racing")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="PitLane", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
from routes.auth import router as auth_router
from routes.races import router as races_router
from routes.cards import router as cards_router
from routes.bets import router as bets_router
from routes.profile import router as profile_router

app.include_router(auth_router)
app.include_router(races_router)
app.include_router(cards_router)
app.include_router(bets_router)
app.include_router(profile_router)

app.mount("/static", StaticFiles(directory="/opt/racing/static"), name="static")


@app.get("/")
async def index():
    return FileResponse("/opt/racing/static/index.html")


@app.get("/race")
async def race_page():
    return FileResponse("/opt/racing/static/race.html")


@app.get("/cards")
async def cards_page():
    return FileResponse("/opt/racing/static/cards.html")


@app.get("/profile")
async def profile_page():
    return FileResponse("/opt/racing/static/profile.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
