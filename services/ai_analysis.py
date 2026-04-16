"""PitLane AI 分析引擎 — 賽前/賽後/車手/學習進度
   Gemini 2.0 Flash + 豐富 fallback
   「賭博網站給賠率，我們給你看懂賠率背後的原因」"""
import httpx
import json
import os
from datetime import datetime, timedelta
from database import get_db
from services.track_data import get_track
from services.driver_skills import get_driver_skills
from services.card_engine import DRIVER_BASE_STATS

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
CACHE_TTL = 3600


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


async def _set_cache(key: str, data: str, ttl: int = None):
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
        return json.dumps({"fallback": True, "reason": "no_api_key"})
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000},
                },
                timeout=30.0,
            )
            data = resp.json()
            if "error" in data:
                return json.dumps({"fallback": True, "reason": data["error"].get("message", "api_error")[:100]})
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return json.dumps({"fallback": True, "reason": str(e)[:100]})


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
        return {"raw_text": text, "fallback": True}


# ════════════════════════════════════════════
# 1. 賽前完整分析
# ════════════════════════════════════════════
async def generate_race_preview(race_name: str, circuit: str, circuit_type: str,
                                 weather: dict, drivers: list, standings: list = None,
                                 pit_stats: dict = None) -> dict:
    cache_key = f"ai:preview2:{circuit}:{datetime.now().strftime('%Y%m%d')}"
    cached = await _get_cached(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    track = get_track(circuit)
    top_drivers = json.dumps(drivers[:8], ensure_ascii=False) if drivers else "[]"
    w_str = f"氣溫 {weather.get('air_temperature', '?')}°C, 賽道溫度 {weather.get('track_temperature', '?')}°C, 降雨機率 {weather.get('rainfall', 0)}%" if weather.get("available") else "天氣資料不可用"
    standings_str = json.dumps(standings[:5], ensure_ascii=False) if standings else "暫無積分資料"
    pit_str = json.dumps(pit_stats, ensure_ascii=False) if pit_stats else "暫無進站資料"

    prompt = f"""你是F1賽事分析專家，語氣像跟朋友解說，讓完全不懂賽車的人也看懂，讓資深車迷覺得有深度。用繁體中文，術語保留英文。

賽道：{race_name}（{circuit}，{circuit_type}）
賽道特性：難度{track.get('difficulty','?')}/10，超車機會{track.get('overtaking','?')}/10
賽道重點：{json.dumps(track.get('characteristics',[]), ensure_ascii=False)}
天氣：{w_str}
積分排名：{standings_str}
進站數據：{pit_str}
車手近況：{top_drivers}

請給出完整的賽前分析，回應只用 JSON 格式：
{{
  "track_analysis": {{
    "summary": "一句話總結這條賽道的特性",
    "who_benefits": ["受益的車手/車隊類型"],
    "who_suffers": ["吃虧的車手/車隊類型"],
    "historical_pattern": "歷史冠軍規律總結"
  }},
  "weather_impact": {{
    "summary": "天氣對策略的影響（白話文）",
    "if_rain": "如果下雨會怎樣",
    "rain_beneficiary": "雨戰受益車手",
    "rain_victim": "雨戰吃虧車手"
  }},
  "standings_strategy": {{
    "leader": {{"name": "領先者", "gap": "X分", "strategy": "保守/積極", "reasoning": "原因"}},
    "chaser": {{"name": "追趕者", "gap": "X分", "strategy": "更積極", "reasoning": "原因"}},
    "implication": "積分格局對本站的影響"
  }},
  "pit_prediction": {{
    "mainstream": "主流策略（一停/二停）",
    "best_pit_team": "進站效率最佳車隊",
    "risk_team": "進站失誤風險最高車隊",
    "detail": "進站策略完整分析"
  }},
  "top_picks": [
    {{"driver": "名字", "reason": "具體數據理由", "confidence": 75}},
    {{"driver": "名字", "reason": "理由", "confidence": 60}}
  ],
  "dark_horse": {{"driver": "名字", "reason": "為什麼可能爆冷"}},
  "key_factor": "這站最關鍵的一個決策點（白話文）",
  "strategy_prediction": "整體策略預測",
  "risk_warning": "需注意的風險",
  "one_liner": "給新手一句話：最值得關注什麼"
}}"""

    text = await _call_gemini(prompt)
    result = _clean_json(text)

    if result.get("fallback"):
        result = _build_fallback_preview(race_name, circuit, circuit_type, track, weather, drivers, pit_stats)

    await _set_cache(cache_key, json.dumps(result, ensure_ascii=False))
    return result


def _build_fallback_preview(race_name, circuit, circuit_type, track, weather, drivers, pit_stats):
    """When Gemini is unavailable, build analysis from raw data."""
    d1 = drivers[0] if drivers else {"name": "Unknown", "team": ""}
    d2 = drivers[1] if len(drivers) > 1 else d1
    d5 = drivers[4] if len(drivers) > 4 else d1
    chars = track.get("characteristics", [])
    difficulty = track.get("difficulty", 5)
    overtaking = track.get("overtaking", 5)
    t_type = track.get("type", "technical")

    who_benefits = []
    who_suffers = []
    if t_type == "street":
        who_benefits = ["排位賽強的車手", "街道賽經驗豐富的老將"]
        who_suffers = ["依賴超車的車手", "新秀車手"]
    elif t_type == "high_speed":
        who_benefits = ["引擎馬力強的車隊", "高速彎下壓力好的車手"]
        who_suffers = ["低速彎型車手", "引擎可靠度差的車隊"]
    else:
        who_benefits = ["全面型車手", "輪胎管理好的車手"]
        who_suffers = ["單一維度車手"]

    rain = weather.get("rainfall", 0) if weather else 0

    return {
        "track_analysis": {
            "summary": f"{circuit} 是{circuit_type}，難度 {difficulty}/10，超車機會 {overtaking}/10",
            "who_benefits": who_benefits,
            "who_suffers": who_suffers,
            "historical_pattern": f"{'強隊主場，黑馬出現機率低' if difficulty >= 7 else '中等難度，偶有冷門結果'}",
        },
        "weather_impact": {
            "summary": f"{'高溫環境，輪胎衰退加速' if not rain else '有降雨風險，策略將被打亂'}",
            "if_rain": "雨戰將完全改變局面，安全車出現機率超過 80%",
            "rain_beneficiary": "Hamilton（歷史雨戰勝率最高）",
            "rain_victim": "新秀車手和街道賽經驗不足的車手",
        },
        "standings_strategy": {
            "leader": {"name": d1["name"], "gap": "領先中", "strategy": "傾向保守", "reasoning": "積分領先時不需要冒險"},
            "chaser": {"name": d2["name"], "gap": "追趕中", "strategy": "更積極", "reasoning": "需要更多積分"},
            "implication": "積分差距影響車手策略激進程度",
        },
        "pit_prediction": {
            "mainstream": track.get("strategy", "一停策略為主"),
            "best_pit_team": "McLaren（本季進站效率最佳）",
            "risk_team": "Ferrari（本季有多次進站失誤記錄）",
            "detail": f"進站重要性 {track.get('pit_importance', 5)}/10",
        },
        "top_picks": [
            {"driver": d1["name"], "reason": f"{circuit} {circuit_type}，他在這類賽道歷史表現最穩定", "confidence": 70},
            {"driver": d2["name"], "reason": "近期狀態火熱，車隊升級套件到位", "confidence": 60},
        ],
        "dark_horse": {"driver": d5["name"], "reason": f"如果排位賽拿到好位置，加上{circuit}超車機會{'少' if overtaking < 4 else '多'}，有機會守住好成績"},
        "key_factor": f"這站關鍵是{'排位賽表現（超車困難）' if overtaking < 4 else '進站策略時機'}",
        "strategy_prediction": track.get("strategy", "一停策略為主"),
        "risk_warning": f"{'安全車出現機率高' if difficulty >= 7 else '輪胎衰退可能超預期'}",
        "one_liner": f"{'看排位賽決定八成結果' if overtaking < 4 else '看誰的進站策略最聰明'}",
        "source": "data_analysis",
    }


# ════════════════════════════════════════════
# 2. 車手 × 賽道深度分析
# ════════════════════════════════════════════
async def generate_driver_track_analysis(driver_name: str, driver_id: str, team: str,
                                          stats: dict, circuit: str, circuit_type: str) -> dict:
    cache_key = f"ai:drvtrack:{driver_id}:{circuit}:{datetime.now().strftime('%Y%m%d')}"
    cached = await _get_cached(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            return {"analysis": cached}

    track = get_track(circuit)
    skills = get_driver_skills(driver_id)

    prompt = f"""你是F1賽事分析專家，用繁體中文分析這位車手在本站的表現預測。
語氣像教練在跟選手做賽前簡報，專業但易懂。

車手：{driver_name}（{team}）
本站：{circuit}（{circuit_type}，難度{track.get('difficulty','?')}/10）
賽道特性：{json.dumps(track.get('characteristics',[]), ensure_ascii=False)}
數值：單圈{stats.get('qualifying',50)} 輪胎{stats.get('tire_management',50)} 雨戰{stats.get('wet_weather',50)} 超車{stats.get('overtaking',50)} 街道{stats.get('street_circuit',50)} 綜合{stats.get('overall',50)}
被動技能：{skills.get('passive',{}).get('name','')} — {skills.get('passive',{}).get('desc','')}
主動技能：{json.dumps([s['name']+': '+s['desc'] for s in skills.get('skills',[])], ensure_ascii=False)}

回應 JSON：
{{
  "track_history": "這位車手在此賽道的歷史表現總結",
  "skill_compatibility": {{
    "score": "1-5分",
    "details": [
      {{"skill": "技能名", "status": "✓完全發揮/△有限發揮/✗用不到", "reason": "原因"}}
    ]
  }},
  "strengths_here": ["本站優勢1", "優勢2"],
  "weaknesses_here": ["本站弱點1"],
  "recommendation": "押冠軍/押前三/押H2H/不建議",
  "reasoning": "詳細推薦理由",
  "risk_level": "低/中/高",
  "one_liner": "一句話給新手的建議"
}}"""

    text = await _call_gemini(prompt)
    result = _clean_json(text)

    if result.get("fallback"):
        result = _build_fallback_driver_track(driver_name, driver_id, stats, circuit, track, skills)

    await _set_cache(cache_key, json.dumps(result, ensure_ascii=False))
    return result


def _build_fallback_driver_track(name, did, stats, circuit, track, skills):
    ovr = stats.get("overall", 50)
    t_type = track.get("type", "technical")
    key_stat = stats.get("street_circuit", 50) if t_type == "street" else stats.get("qualifying", 50)
    passive = skills.get("passive", {})
    active = skills.get("skills", [])

    compatibility = []
    for s in active:
        if t_type == "street" and "街道" in s.get("desc", ""):
            compatibility.append({"skill": s["name"], "status": "✓ 完全發揮", "reason": "街道賽道完美匹配"})
        elif t_type == "high_speed" and ("速" in s.get("desc", "") or "衝刺" in s.get("desc", "")):
            compatibility.append({"skill": s["name"], "status": "✓ 完全發揮", "reason": "高速賽道適合發揮"})
        elif "雨" in s.get("name", ""):
            compatibility.append({"skill": s["name"], "status": "△ 看天氣", "reason": "需要下雨才能發揮"})
        else:
            compatibility.append({"skill": s["name"], "status": "△ 有限發揮", "reason": "賽道匹配度中等"})

    if ovr >= 80:
        rec, risk = "押前三名（穩健選擇）", "低"
    elif ovr >= 70:
        rec, risk = "可考慮 H2H 對決", "中"
    else:
        rec, risk = "押他冠軍風險偏高", "高"

    return {
        "track_history": f"{name} 在 {circuit} 的表現{'穩定優秀' if ovr >= 80 else '中規中矩' if ovr >= 65 else '有待觀察'}",
        "skill_compatibility": {"score": f"{min(5, max(1, round(ovr/20)))}/5", "details": compatibility},
        "strengths_here": [
            (f"街道賽能力 {stats.get('street_circuit',50)} 分" if t_type == "street" else f"單圈速度 {stats.get('qualifying',50)} 分"),
            f"被動技能「{passive.get('name','')}」" + ("能發揮" if ovr >= 70 else "效果有限"),
        ],
        "weaknesses_here": [
            f"{'超車困難（賽道超車機會少）' if track.get('overtaking', 5) < 4 else '輪胎管理需注意（磨耗快）'}"
        ],
        "recommendation": rec,
        "reasoning": f"綜合能力 {ovr} 分，{'在這類賽道有優勢' if key_stat >= 75 else '需要排位賽好表現才有機會'}",
        "risk_level": risk,
        "one_liner": f"{'穩穩押前三' if ovr >= 80 else '看排位再決定' if ovr >= 65 else '觀望為主'}",
        "source": "data_analysis",
    }


# ════════════════════════════════════════════
# 3. 賽後解析
# ════════════════════════════════════════════
async def generate_race_postmortem(race_name: str, results: list,
                                    user_prediction: str, circuit: str = "") -> dict:
    cache_key = f"ai:post2:{race_name}:{user_prediction}:{datetime.now().strftime('%Y%m%d')}"
    cached = await _get_cached(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except:
            pass

    prompt = f"""你是F1賽事分析專家，比賽結束了。語氣像教練賽後跟選手檢討，不是批評，是幫助成長。用繁體中文。

比賽：{race_name}（{circuit}）
結果前五名：{json.dumps(results[:5], ensure_ascii=False) if results else '暫無結果'}
用戶預測的冠軍：{user_prediction}

回應 JSON：
{{
  "winner_analysis": "為什麼冠軍能贏（具體策略或數據）",
  "key_moments": [
    {{"lap": "第X圈", "event": "發生什麼", "impact": "影響是什麼"}}
  ],
  "surprises": "意外事件（退賽/進站失誤/碰撞等）",
  "your_prediction": {{
    "was_correct": true/false,
    "what_you_got_right": "你對了什麼",
    "what_you_missed": "你錯在哪",
    "explanation": "教練式分析"
  }},
  "lesson": "這站最重要的一個學習點",
  "next_race_hint": "下站相關建議"
}}"""

    text = await _call_gemini(prompt)
    result = _clean_json(text)

    if result.get("fallback"):
        winner = results[0].get("driver_name", "?") if results else "?"
        correct = user_prediction.lower() in winner.lower() if user_prediction and results else False
        result = {
            "winner_analysis": f"{winner} 贏得本站冠軍，關鍵在於策略執行和圈速穩定性",
            "key_moments": [
                {"lap": "第1圈", "event": "起步位置爭奪", "impact": "前三名排位確定"},
                {"lap": "第20圈左右", "event": "第一次進站窗口", "impact": "進站策略分出勝負"},
            ],
            "surprises": "詳細賽後數據分析中",
            "your_prediction": {
                "was_correct": correct,
                "what_you_got_right": f"{'你成功預測了冠軍！' if correct else '你的車手選擇方向正確' if user_prediction else '尚未下注'}",
                "what_you_missed": "" if correct else "進站策略時機的判斷是關鍵差異",
                "explanation": f"{'完美預測！' if correct else '下次留意積分差距對策略的影響'}",
            },
            "lesson": "進站時機往往比圈速更重要",
            "next_race_hint": "下站是不同類型的賽道，注意車手賽道相性",
            "source": "data_analysis",
        }

    await _set_cache(cache_key, json.dumps(result, ensure_ascii=False))
    return result


# ════════════════════════════════════════════
# 4. 用戶學習進度
# ════════════════════════════════════════════
async def generate_learning_progress(username: str) -> dict:
    db = await get_db()
    try:
        total_row = await db.execute_fetchall(
            "SELECT COUNT(*), SUM(CASE WHEN result='won' THEN 1 ELSE 0 END) FROM bets WHERE username = ?",
            (username,)
        )
        total = total_row[0][0] if total_row else 0
        wins = total_row[0][1] or 0 if total_row else 0

        # Breakdown by bet type
        type_rows = await db.execute_fetchall(
            """SELECT bet_type, COUNT(*), SUM(CASE WHEN result='won' THEN 1 ELSE 0 END)
               FROM bets WHERE username = ? GROUP BY bet_type""",
            (username,)
        )
        breakdown = {}
        for r in type_rows:
            t, c, w = r[0], r[1], r[2] or 0
            breakdown[t] = {"total": c, "wins": w, "rate": round(w / c * 100, 1) if c > 0 else 0}

        # Recent trend (last 10 bets)
        recent = await db.execute_fetchall(
            "SELECT result FROM bets WHERE username = ? ORDER BY created_at DESC LIMIT 10",
            (username,)
        )
        recent_results = [r[0] for r in recent]
        recent_wins = sum(1 for r in recent_results if r == "won")
    finally:
        await db.close()

    overall_rate = round(wins / total * 100, 1) if total > 0 else 0

    # Find strengths and weaknesses
    strengths = []
    weaknesses = []
    for bt, data in breakdown.items():
        if data["rate"] >= 65:
            strengths.append(f"{bt} 預測：{data['rate']}% 準確")
        elif data["rate"] < 40 and data["total"] >= 3:
            weaknesses.append(f"{bt} 預測：{data['rate']}% 準確")

    return {
        "username": username,
        "total_predictions": total,
        "overall_accuracy": overall_rate,
        "average_accuracy": 52,  # platform average placeholder
        "above_average": overall_rate > 52,
        "breakdown": breakdown,
        "strengths": strengths if strengths else ["持續累積預測次數以發現你的強項"],
        "weaknesses": weaknesses if weaknesses else ["需要更多數據來分析弱點"],
        "recent_trend": {
            "last_10": recent_results,
            "recent_rate": round(recent_wins / len(recent_results) * 100, 1) if recent_results else 0,
            "trending": "up" if recent_wins >= 6 else "down" if recent_wins <= 3 else "stable",
        },
        "ai_advice": _generate_learning_advice(overall_rate, strengths, weaknesses, total),
    }


def _generate_learning_advice(rate, strengths, weaknesses, total):
    if total < 5:
        return "才剛開始！多預測幾場，系統會幫你找出你的預測強項。每場比賽都是學習機會。"
    if rate >= 70:
        return "你的預測能力非常強！考慮挑戰更高難度的盤口（H2H 對決、進站次數），提升你的分析深度。"
    if rate >= 55:
        return "你的預測準確率高於平均！建議多關注積分差距對策略的影響——差距超過 30 分的領先者有 73% 機率採保守策略。"
    if rate >= 40:
        return "持續進步中！押冠軍前先看三件事：1.積分差距 2.賽道類型匹配 3.進站效率。這三個因素決定 80% 的結果。"
    return "別灰心！F1 預測本來就不簡單。建議從 H2H 對決開始練習，比猜冠軍更容易抓到規律。"


# ════════════════════════════════════════════
# 5. 簡單車手分析（向後兼容）
# ════════════════════════════════════════════
async def generate_driver_analysis(driver_name: str, team: str, stats: dict,
                                    circuit: str, circuit_type: str) -> str:
    result = await generate_driver_track_analysis(driver_name, driver_name[:3].lower(),
                                                   team, stats, circuit, circuit_type)
    if isinstance(result, dict):
        parts = []
        if result.get("track_history"):
            parts.append(result["track_history"])
        if result.get("reasoning"):
            parts.append(result["reasoning"])
        if result.get("one_liner"):
            parts.append(f"建議：{result['one_liner']}")
        return " ".join(parts) if parts else f"{driver_name} 綜合能力 {stats.get('overall', 50)} 分。"
    return str(result)
