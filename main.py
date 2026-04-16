import sys
sys.path.insert(0, "/opt/racing")

from dotenv import load_dotenv
load_dotenv("/opt/racing/.env")

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


app = FastAPI(title="PitLane", version="2.0.0", lifespan=lifespan)

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
from routes.p2p import router as p2p_router
from routes.challenge import router as challenge_router

app.include_router(auth_router)
app.include_router(races_router)
app.include_router(cards_router)
app.include_router(bets_router)
app.include_router(profile_router)
app.include_router(p2p_router)
app.include_router(challenge_router)

# AI analysis + track + odds endpoints
from fastapi import APIRouter, Header
from routes.auth import get_current_user
from services.ai_analysis import generate_race_preview, generate_driver_analysis
from services.track_data import get_track, get_all_tracks
from services.pit_analysis import get_team_pit_stats
from services.odds_engine import get_market_odds
from services import openf1

extra = APIRouter(tags=["extra"])


@extra.get("/api/tracks")
async def all_tracks():
    return get_all_tracks()


@extra.get("/api/tracks/{circuit}")
async def track_info(circuit: str):
    return get_track(circuit)


@extra.get("/api/races/{race_id}/analysis")
async def race_analysis(race_id: str):
    """AI 賽前分析"""
    from routes.races import current_race
    race = await current_race()
    drivers_data = await cards_router.routes[0].endpoint()  # /api/drivers
    weather = {}
    if race.get("session_key"):
        try:
            weather = await openf1.get_weather(race["session_key"])
            weather = weather[-1] if weather else {}
            weather["available"] = True
        except:
            weather = {"available": False}

    drivers_list = [{"name": d["name"], "team": d.get("team", ""), "points": d.get("points", 0)}
                    for d in drivers_data.get("drivers", [])[:8]]

    return await generate_race_preview(
        race.get("race_name", ""), race.get("circuit", ""),
        race.get("circuit_type", "技術型賽道"), weather, drivers_list
    )


@extra.get("/api/drivers/{driver_id}/analysis")
async def driver_analysis(driver_id: str):
    """AI 車手深度分析"""
    from routes.cards import driver_card
    card = await driver_card(driver_id)
    from routes.races import current_race
    race = await current_race()
    return {"analysis": await generate_driver_analysis(
        card["name"], card.get("team", ""), card.get("stats", {}),
        race.get("circuit", ""), race.get("circuit_type", "")
    )}


@extra.get("/api/races/{race_id}/odds")
async def race_odds(race_id: str):
    """全場賠率表"""
    from routes.cards import list_drivers
    data = await list_drivers()
    from routes.races import current_race
    race = await current_race()
    return {"odds": get_market_odds(data.get("drivers", []), race.get("circuit", ""))}


@extra.get("/api/teams/{team}/pit-stats")
async def team_pit_stats(team: str):
    """車隊進站數據"""
    from routes.races import current_race
    race = await current_race()
    sk = race.get("session_key")
    if not sk:
        return {"error": "No session key"}
    stats = await get_team_pit_stats(sk)
    return stats.get(team, {"error": "Team not found", "available_teams": list(stats.keys())})


@extra.get("/api/pit-stats")
async def all_pit_stats():
    """所有車隊進站數據"""
    from routes.races import current_race
    race = await current_race()
    sk = race.get("session_key")
    if not sk:
        return {}
    return await get_team_pit_stats(sk)


app.include_router(extra)

# Share card image generation
from fastapi.responses import StreamingResponse
from services.share_card import generate_share_card_image

@app.get("/api/profile/sharecard/image")
async def sharecard_image(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    img_bytes = await generate_share_card_image(user["username"])
    return StreamingResponse(img_bytes, media_type="image/png",
                            headers={"Content-Disposition": "inline; filename=pitlane-card.png"})


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

@app.get("/battle")
async def battle_page():
    return FileResponse("/opt/racing/static/battle.html")

@app.get("/leaderboard")
async def leaderboard_page():
    return FileResponse("/opt/racing/static/leaderboard.html")

@app.get("/history")
async def history_page():
    return FileResponse("/opt/racing/static/history.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
