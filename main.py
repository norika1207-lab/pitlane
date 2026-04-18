import sys
sys.path.insert(0, "/opt/racing")

from dotenv import load_dotenv
load_dotenv("/opt/racing/.env")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Throttenix", version="2.0.0", lifespan=lifespan)

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
from routes.rpg import router as rpg_router
from routes.historical import router as historical_router
from routes.halloffame import router as halloffame_router

app.include_router(auth_router)
app.include_router(races_router)
app.include_router(cards_router)
app.include_router(bets_router)
app.include_router(profile_router)
app.include_router(p2p_router)
app.include_router(challenge_router)
app.include_router(rpg_router)
app.include_router(historical_router)
app.include_router(halloffame_router)

# AI analysis + track + odds endpoints
from fastapi import APIRouter, Header
from routes.auth import get_current_user
from services.ai_analysis import (generate_race_preview, generate_driver_analysis,
    generate_driver_track_analysis, generate_race_postmortem, generate_learning_progress)
from services.track_data import get_track, get_all_tracks
from services.pit_analysis import get_team_pit_stats, get_session_pit_leaderboard
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
    """AI full pre-race analysis (circuit + weather + standings + pit stops + recommendations)"""
    from routes.races import current_race
    race = await current_race()
    drivers_data = await cards_router.routes[0].endpoint()
    weather = {}
    if race.get("session_key"):
        try:
            w = await openf1.get_weather(race["session_key"])
            weather = w[-1] if w else {}
            weather["available"] = True
        except:
            weather = {"available": False}

    drivers_list = [{"name": d["name"], "team": d.get("team", ""), "points": d.get("points", 0)}
                    for d in drivers_data.get("drivers", [])[:8]]

    # Get pit stats
    pit_stats = None
    if race.get("session_key"):
        try:
            pit_stats = await get_team_pit_stats(race["session_key"])
        except:
            pass

    return await generate_race_preview(
        race.get("race_name", ""), race.get("circuit", ""),
        race.get("circuit_type", "Technical Circuit"), weather, drivers_list,
        pit_stats=pit_stats
    )


@extra.get("/api/drivers/{driver_id}/analysis")
async def driver_analysis(driver_id: str):
    """AI driver × circuit in-depth analysis"""
    from routes.cards import driver_card
    card = await driver_card(driver_id)
    from routes.races import current_race
    race = await current_race()
    return await generate_driver_track_analysis(
        card["name"], driver_id, card.get("team", ""), card.get("stats", {}),
        race.get("circuit", ""), race.get("circuit_type", "")
    )


@extra.get("/api/races/{race_id}/postmortem")
async def race_postmortem(race_id: str, prediction: str = "", authorization: str = Header(None)):
    """Post-race analysis + personal prediction review"""
    from routes.races import current_race
    race = await current_race()
    # Try to get user's prediction
    if authorization and authorization.startswith("Bearer "):
        try:
            user = await get_current_user(authorization)
            db = await get_db()
            try:
                rows = await db.execute_fetchall(
                    "SELECT prediction FROM bets WHERE username = ? AND race_id = ? LIMIT 1",
                    (user["username"], race_id)
                )
                if rows:
                    prediction = rows[0][0]
            finally:
                await db.close()
        except:
            pass
    return await generate_race_postmortem(
        race.get("race_name", ""), [], prediction, race.get("circuit", "")
    )


@extra.get("/api/profile/learning-progress")
async def learning_progress(authorization: str = Header(None)):
    """User learning progress tracker"""
    user = await get_current_user(authorization)
    return await generate_learning_progress(user["username"])


@extra.get("/api/content/{category}")
async def get_content(category: str):
    """Get pre-generated content by category."""
    # Normalise: hyphens→underscores, handle plural/singular aliases
    cat_map = {
        "classic-races": "classic_race",
        "classic-race": "classic_race",
        "drivers": "driver_profile",
        "driver-profiles": "driver_profile",
        "teams": "team_profile",
        "team-profiles": "team_profile",
        "tracks": "track_analysis",
        "track-analyses": "track_analysis",
        "postmortems": "race_postmortem",
        "race-postmortems": "race_postmortem",
        "rivalries": "rivalry",
        "trends": "trend",
    }
    db_category = cat_map.get(category, category.replace("-", "_"))
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT key, title, data FROM content_cache WHERE category = ? ORDER BY created_at DESC",
            (db_category,),
        )
        import json
        items = []
        for r in rows:
            try:
                data = json.loads(r[2])
            except:
                data = {"raw": r[2]}
            items.append({"key": r[0], "title": r[1], "data": data})
        return {"category": category, "count": len(items), "items": items}
    finally:
        await db.close()


@extra.get("/api/content/{category}/{key}")
async def get_content_item(category: str, key: str):
    """Get single content item."""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT title, data FROM content_cache WHERE key = ?", (key,),
        )
        if not rows:
            return {"error": "Not found"}
        import json
        try:
            data = json.loads(rows[0][1])
        except:
            data = {"raw": rows[0][1]}
        return {"key": key, "title": rows[0][0], "data": data}
    finally:
        await db.close()


@extra.get("/api/races/{race_id}/odds")
async def race_odds(race_id: str):
    """Full race odds table"""
    from routes.cards import list_drivers
    data = await list_drivers()
    from routes.races import current_race
    race = await current_race()
    return {"odds": get_market_odds(data.get("drivers", []), race.get("circuit", ""))}


@extra.get("/api/teams/{team}/pit-stats")
async def team_pit_stats(team: str):
    """Team pit stop data"""
    from routes.races import current_race
    race = await current_race()
    sk = race.get("session_key")
    if not sk:
        return {"error": "No session key"}
    stats = await get_team_pit_stats(sk)
    return stats.get(team, {"error": "Team not found", "available_teams": list(stats.keys())})


@extra.get("/api/pit-stats")
async def all_pit_stats(session_key: int | None = None):
    """All team pit stop data. Accepts ?session_key= to analyze a specific session."""
    sk = session_key
    if not sk:
        from routes.races import current_race
        race = await current_race()
        sk = race.get("session_key")
    if not sk:
        return {}
    return await get_team_pit_stats(sk)


@extra.get("/api/pit-leaderboard")
async def pit_leaderboard(session_key: int | None = None, limit: int = 10):
    """Fastest individual pit stops of the session."""
    sk = session_key
    if not sk:
        from routes.races import current_race
        race = await current_race()
        sk = race.get("session_key")
    if not sk:
        return {"entries": [], "session_key": None}
    entries = await get_session_pit_leaderboard(sk, limit=limit)
    return {"entries": entries, "session_key": sk}


app.include_router(extra)

# Share card image generation
from fastapi.responses import StreamingResponse
from services.share_card import generate_share_card_image

@app.get("/api/profile/sharecard/image")
async def sharecard_image(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    img_bytes = await generate_share_card_image(user["username"])
    return StreamingResponse(img_bytes, media_type="image/png",
                            headers={"Content-Disposition": "inline; filename=throttenix-card.png"})


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

@app.get("/halloffame")
async def halloffame_page():
    return FileResponse("/opt/racing/static/halloffame.html")

@app.get("/car-explorer")
async def car_explorer_page():
    return FileResponse("/opt/racing/static/car_explorer.html")

@app.get("/collection")
async def collection_page():
    return FileResponse("/opt/racing/static/collection.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
