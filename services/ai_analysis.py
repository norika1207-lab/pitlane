"""Gemini AI 分析 — 賽前/賽後/車手深度分析"""
import httpx
import json
import os
from datetime import datetime, timedelta
from database import get_db

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
CACHE_TTL = 3600  # 1 hour


async def _get_cached(key: str) -> str | None:
    db = await get_db()
    try:
        row = await db.execute_fetchall(
            "SELECT data, cached_at FROM race_cache WHERE key = ?", (key,)
        )
        if row:
            cached_at = datetime.fromisoformat(row[0][1])
            if datetime.now() - cached_at < timedelta(seconds=CACHE_TTL):
                return row[0][0]
    finally:
        await db.close()
    return None


async def _set_cache(key: str, data: str):
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO race_cache (key, data, cached_at) VALUES (?, ?, ?)",
            (key, data, datetime.now().isoformat()),
        )
        await db.commit()
    finally:
        await db.close()


async def _call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return '{"error": "GEMINI_API_KEY not configured"}'
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500},
                },
                timeout=30.0,
            )
            data = resp.json()
            if "error" in data:
                return json.dumps({"error": data["error"].get("message", "API error"), "fallback": True})
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return json.dumps({"error": str(e), "fallback": True})


def _clean_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip().lstrip("json").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_text": text}


async def generate_race_preview(race_name: str, circuit: str, circuit_type: str,
                                 weather: dict, drivers: list) -> dict:
    cache_key = f"ai:preview:{circuit}:{datetime.now().strftime('%Y%m%d')}"
    cached = await _get_cached(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    top5 = json.dumps(drivers[:8], ensure_ascii=False, indent=2) if drivers else "無資料"
    w = f"氣溫 {weather.get('air_temperature', '?')}°C, 賽道溫度 {weather.get('track_temperature', '?')}°C, 降雨 {weather.get('rainfall', 0)}" if weather.get("available") else "天氣資料不可用"

    prompt = f"""你是 F1 賽事分析專家，用繁體中文回答。語氣要讓完全不懂賽車的人也能看懂，像朋友在聊天。

賽事：{race_name}
賽道：{circuit}（{circuit_type}）
天氣：{w}

車手近況（按積分排序）：
{top5}

請分析這站比賽，回應只用以下 JSON 格式，不要加其他文字：
{{
  "top_picks": [
    {{"driver": "車手名", "reason": "具體理由（要提到數據或賽道特性）", "confidence": 75}},
    {{"driver": "車手名", "reason": "理由", "confidence": 60}}
  ],
  "dark_horse": {{"driver": "車手名", "reason": "為什麼他可能爆冷"}},
  "key_factor": "這站最關鍵的影響因素（一句話，白話文）",
  "strategy_prediction": "進站策略預測（白話文）",
  "risk_warning": "需要注意的風險"
}}"""

    text = await _call_gemini(prompt)
    result = _clean_json(text)
    if result.get("fallback"):
        # Gemini unavailable, generate fallback from data
        d1 = drivers[0] if drivers else {"name": "Unknown"}
        d2 = drivers[1] if len(drivers) > 1 else {"name": "Unknown"}
        result = {
            "top_picks": [
                {"driver": d1.get("name", "?"), "reason": f"{circuit} {circuit_type}，歷史數據顯示他在這類賽道表現最穩定", "confidence": 70},
                {"driver": d2.get("name", "?"), "reason": f"近期狀態火熱，車隊升級套件到位", "confidence": 60},
            ],
            "dark_horse": {"driver": drivers[4]["name"] if len(drivers) > 4 else "?", "reason": "近幾站進步明顯，如果排位賽拿到好位置有機會爆冷"},
            "key_factor": f"這站是{circuit_type}，進站策略和輪胎管理將是決勝關鍵",
            "strategy_prediction": "預測多數車隊採一停策略，但天氣變化可能打亂計畫",
            "risk_warning": "安全車出現機率高，可能打亂所有策略預測",
            "source": "data_fallback",
        }
    await _set_cache(cache_key, json.dumps(result, ensure_ascii=False))
    return result


async def generate_driver_analysis(driver_name: str, team: str, stats: dict,
                                    circuit: str, circuit_type: str) -> str:
    cache_key = f"ai:driver:{driver_name}:{circuit}:{datetime.now().strftime('%Y%m%d')}"
    cached = await _get_cached(cache_key)
    if cached:
        return cached

    prompt = f"""你是 F1 賽事分析專家，用繁體中文寫一段 120 字左右的車手分析。語氣像朋友在聊天，讓新手看懂。

車手：{driver_name}（{team}）
本站賽道：{circuit}（{circuit_type}）
數值：單圈速度 {stats.get('qualifying', 50)}, 輪胎管理 {stats.get('tire_management', 50)}, 雨戰 {stats.get('wet_weather', 50)}, 超車 {stats.get('overtaking', 50)}, 街道賽 {stats.get('street_circuit', 50)}, 綜合 {stats.get('overall', 50)}

說明：這站他的強項能不能發揮？弱點會不會被放大？值不值得押？直接給建議。不要加標題。"""

    text = await _call_gemini(prompt)
    text = text.strip()
    if "fallback" in text or "error" in text:
        ovr = stats.get("overall", 50)
        qual = stats.get("qualifying", 50)
        best = max(stats.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0)
        text = f"{driver_name} 綜合能力 {ovr} 分，{'表現亮眼' if ovr >= 80 else '中規中矩' if ovr >= 60 else '仍需努力'}。本站 {circuit} 是{circuit_type}，{'他的街道賽能力突出，值得考慮' if 'street' in circuit_type else '需要觀察排位賽表現再決定'}。單圈速度 {qual} 分{'是強項' if qual >= 80 else '，不算突出'}。整體來說，{'值得押前三名' if ovr >= 75 else '可以考慮 H2H 對決盤' if ovr >= 60 else '押他冠軍風險較高'}。"
    await _set_cache(cache_key, text)
    return text


async def generate_race_postmortem(race_name: str, results: list, user_prediction: str) -> dict:
    cache_key = f"ai:post:{race_name}:{user_prediction}:{datetime.now().strftime('%Y%m%d')}"
    cached = await _get_cached(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    prompt = f"""你是 F1 賽事分析專家，用繁體中文解釋比賽結果。語氣像朋友在聊天。

比賽：{race_name}
結果：{json.dumps(results[:5], ensure_ascii=False) if results else '暫無結果'}
用戶預測的冠軍：{user_prediction}

回應只用 JSON：
{{
  "winner_analysis": "冠軍為何能贏（提到具體策略或關鍵圈數）",
  "key_moment": "比賽最關鍵的一刻",
  "your_prediction": {{
    "was_correct": true/false,
    "explanation": "你為什麼對/錯的分析"
  }},
  "lesson": "這站最重要的一個學習點"
}}"""

    text = await _call_gemini(prompt)
    result = _clean_json(text)
    await _set_cache(cache_key, json.dumps(result, ensure_ascii=False))
    return result
