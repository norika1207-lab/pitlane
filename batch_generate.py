"""PitLane 批量內容生成 — 用 Claude Sonnet 一次性產出所有分析存入 DB"""
import sys, os, json, time, sqlite3
sys.path.insert(0, "/opt/racing")
from dotenv import load_dotenv
load_dotenv("/opt/racing/.env")

import anthropic
from services.track_data import TRACKS
from services.driver_skills import DRIVER_SKILLS
from services.card_engine import DRIVER_BASE_STATS

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
DB_PATH = "/opt/racing/pitlane.db"

# Ensure table exists
conn = sqlite3.connect(DB_PATH)
conn.execute("""CREATE TABLE IF NOT EXISTS content_cache (
    key TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")
conn.commit()

total_input = 0
total_output = 0
generated = 0


def call_claude(prompt: str) -> str:
    global total_input, total_output, generated
    r = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    total_input += r.usage.input_tokens
    total_output += r.usage.output_tokens
    generated += 1
    text = r.content[0].text
    print(f"  [{generated}] in={r.usage.input_tokens} out={r.usage.output_tokens} total={total_input+total_output}")
    return text


def save(key: str, category: str, title: str, data):
    if isinstance(data, dict) or isinstance(data, list):
        data = json.dumps(data, ensure_ascii=False)
    conn.execute(
        "INSERT OR REPLACE INTO content_cache (key, category, title, data) VALUES (?, ?, ?, ?)",
        (key, category, title, data),
    )
    conn.commit()


def clean_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip().lstrip("json").strip()
    try:
        return json.loads(text)
    except:
        return {"raw_text": text}


# ════════════════════════════════════════════
# 1. 車手個人檔案（22 位）
# ════════════════════════════════════════════
DRIVERS_2026 = [
    ("nor", "Lando Norris", "McLaren", "1"),
    ("ver", "Max Verstappen", "Red Bull Racing", "3"),
    ("lec", "Charles Leclerc", "Ferrari", "16"),
    ("ham", "Lewis Hamilton", "Ferrari", "44"),
    ("pia", "Oscar Piastri", "McLaren", "81"),
    ("rus", "George Russell", "Mercedes", "63"),
    ("sai", "Carlos Sainz", "Williams", "55"),
    ("alo", "Fernando Alonso", "Aston Martin", "14"),
    ("gas", "Pierre Gasly", "Alpine", "10"),
    ("tsu", "Yuki Tsunoda", "Racing Bulls", "22"),
    ("str", "Lance Stroll", "Aston Martin", "18"),
    ("hul", "Nico Hulkenberg", "Audi", "27"),
    ("law", "Liam Lawson", "Red Bull Racing", "6"),
    ("ant", "Andrea Kimi Antonelli", "Mercedes", "12"),
    ("bea", "Oliver Bearman", "Haas", "87"),
    ("had", "Isack Hadjar", "Racing Bulls", "5"),
    ("bor", "Gabriel Bortoleto", "Audi", "5"),
    ("doo", "Jack Doohan", "Alpine", "7"),
    ("oco", "Esteban Ocon", "Haas", "31"),
]

print("═══ 1/7 車手個人檔案 ═══")
for did, name, team, num in DRIVERS_2026:
    print(f"  Generating: {name}...")
    stats = DRIVER_BASE_STATS.get(did, {})
    skills = DRIVER_SKILLS.get(did, {})
    prompt = f"""你是 F1 賽事分析專家，用繁體中文寫一份車手檔案。語氣專業但親切，讓新手也能看懂。

車手：{name}（#{num}，{team}）
能力值：單圈速度{stats.get('q',50)} 輪胎管理{stats.get('t',50)} 雨戰{stats.get('w',50)} 超車{stats.get('o',50)} 街道賽{stats.get('s',50)}
被動技能：{skills.get('passive',{}).get('name','')} — {skills.get('passive',{}).get('desc','')}
主動技能：{json.dumps([s['name']+': '+s['desc'] for s in skills.get('skills',[])], ensure_ascii=False)}

回應 JSON：
{{
  "bio": "50字個人簡介",
  "driving_style": "駕駛風格描述（30字）",
  "strengths": ["強項1", "強項2", "強項3"],
  "weaknesses": ["弱點1", "弱點2"],
  "career_highlights": ["生涯亮點1", "生涯亮點2"],
  "fun_fact": "一個有趣的冷知識",
  "prediction_tip": "押注建議（什麼時候該押他，什麼時候不該）",
  "rival": "主要競爭對手是誰，為什麼"
}}"""
    text = call_claude(prompt)
    save(f"driver:{did}", "driver_profile", name, clean_json(text))
    time.sleep(0.5)


# ════════════════════════════════════════════
# 2. 車隊深度分析（10 支）
# ════════════════════════════════════════════
TEAMS = [
    ("mclaren", "McLaren", "Andrea Stella", "Lando Norris / Oscar Piastri"),
    ("red_bull", "Red Bull Racing", "Christian Horner", "Max Verstappen / Liam Lawson"),
    ("ferrari", "Ferrari", "Frédéric Vasseur", "Charles Leclerc / Lewis Hamilton"),
    ("mercedes", "Mercedes", "Toto Wolff", "George Russell / Andrea Kimi Antonelli"),
    ("aston_martin", "Aston Martin", "Mike Krack", "Fernando Alonso / Lance Stroll"),
    ("alpine", "Alpine", "Oliver Oakes", "Pierre Gasly / Jack Doohan"),
    ("williams", "Williams", "James Vowles", "Carlos Sainz / Alex Albon"),
    ("haas", "Haas", "Ayao Komatsu", "Oliver Bearman / Esteban Ocon"),
    ("racing_bulls", "Racing Bulls", "Laurent Mekies", "Yuki Tsunoda / Isack Hadjar"),
    ("audi", "Audi (Kick Sauber)", "Mattia Binotto", "Nico Hulkenberg / Gabriel Bortoleto"),
]

print("\n═══ 2/7 車隊深度分析 ═══")
for tid, name, boss, drivers in TEAMS:
    print(f"  Generating: {name}...")
    prompt = f"""你是 F1 賽事分析專家，用繁體中文寫一份車隊分析報告。

車隊：{name}
領隊：{boss}
車手陣容：{drivers}

回應 JSON：
{{
  "overview": "60字車隊概況",
  "car_philosophy": "賽車設計理念（30字）",
  "strengths": ["車隊強項1", "強項2"],
  "weaknesses": ["弱點1", "弱點2"],
  "pit_crew_rating": "進站效率評價（快/中/慢+原因）",
  "strategy_style": "策略風格（保守/激進/靈活）",
  "season_outlook": "本季展望（50字）",
  "best_track_types": ["適合的賽道類型"],
  "betting_tip": "押注建議：什麼情況下押這隊的車手"
}}"""
    text = call_claude(prompt)
    save(f"team:{tid}", "team_profile", name, clean_json(text))
    time.sleep(0.5)


# ════════════════════════════════════════════
# 3. 賽道完整分析（14 條）
# ════════════════════════════════════════════
print("\n═══ 3/7 賽道完整分析 ═══")
for circuit, data in TRACKS.items():
    print(f"  Generating: {data.get('name_zh', circuit)}...")
    prompt = f"""你是 F1 賽事分析專家，用繁體中文寫一份賽道分析報告。讓新手一讀就懂這條賽道的重點。

賽道：{data.get('name_zh',circuit)}（{data.get('name_en',circuit)}）
類型：{data.get('type','technical')} | 難度：{data.get('difficulty',5)}/10 | 超車機會：{data.get('overtaking',5)}/10
夜賽：{'是' if data.get('night_race') else '否'}
特性：{json.dumps(data.get('characteristics',[]), ensure_ascii=False)}
策略：{data.get('strategy','')}

回應 JSON：
{{
  "overview": "60字賽道概況（讓新手秒懂）",
  "key_corners": ["重點彎道1：描述", "重點彎道2：描述"],
  "overtaking_zones": ["超車點1", "超車點2"],
  "tire_strategy": "輪胎策略建議",
  "weather_factor": "天氣對這條賽道的影響",
  "safety_car_probability": "安全車出現機率（高/中/低）及原因",
  "who_wins_here": "什麼類型的車手/車隊在這裡有優勢",
  "historical_drama": "這條賽道歷史上最戲劇性的事件",
  "newbie_tip": "給新手一句話：看這場比賽要注意什麼"
}}"""
    text = call_claude(prompt)
    save(f"track:{circuit}", "track_analysis", data.get("name_zh", circuit), clean_json(text))
    time.sleep(0.5)


# ════════════════════════════════════════════
# 4. 2026 已完成賽事賽後解析
# ════════════════════════════════════════════
RACES_2026 = [
    ("R1", "澳洲大獎賽", "Melbourne", "Norris 奪冠，Verstappen 第二"),
    ("R2", "中國大獎賽", "Shanghai", "Piastri 奪冠，Norris 第二，McLaren 包辦前二"),
    ("R3", "日本大獎賽", "Suzuka", "Verstappen 奪冠，展現鈴鹿統治力"),
    ("R4", "巴林大獎賽", "Sakhir", "Leclerc 奪冠，Hamilton 第二，Ferrari 回勇"),
]

print("\n═══ 4/7 已完成賽事解析 ═══")
for rid, name, circuit, result_summary in RACES_2026:
    print(f"  Generating: {name}...")
    prompt = f"""你是 F1 賽事分析專家，用繁體中文寫一份賽後解析報告。語氣像教練賽後檢討，幫助讀者理解比賽。

比賽：{name}（{circuit}）
結果摘要：{result_summary}

回應 JSON：
{{
  "winner_analysis": "冠軍為何能贏（要有具體策略分析）",
  "key_moments": [
    {{"lap": "第X圈", "event": "發生什麼", "impact": "影響是什麼"}},
    {{"lap": "第X圈", "event": "發生什麼", "impact": "影響"}}
  ],
  "strategy_breakdown": "各車隊策略對比分析",
  "surprise": "這場比賽最意外的事",
  "championship_impact": "對冠軍爭奪的影響",
  "lesson": "這場比賽教我們什麼（給預測玩家的啟示）",
  "highlight_quote": "一句話總結這場比賽"
}}"""
    text = call_claude(prompt)
    save(f"race_post:{rid}", "race_postmortem", name, clean_json(text))
    time.sleep(0.5)


# ════════════════════════════════════════════
# 5. 經典賽事分析（2020-2024 精選）
# ════════════════════════════════════════════
CLASSIC_RACES = [
    ("2021_abudhabi", "2021 阿布達比大獎賽", "Hamilton vs Verstappen 最後一圈逆轉，史上最爭議的冠軍決定戰"),
    ("2022_silverstone", "2022 英國大獎賽", "周冠宇嚴重翻車但安然無恙，Sainz 拿下生涯首勝"),
    ("2023_vegas", "2023 拉斯維加斯大獎賽", "Verstappen 在賭城封王，F1 重返拉斯維加斯"),
    ("2024_monaco", "2024 摩納哥大獎賽", "Leclerc 終於在主場奪冠，全場車迷瘋狂"),
    ("2020_sakhir", "2020 巴林外圈大獎賽", "Grosjean 嚴重撞車起火但生還，Perez 從最後一名逆轉奪冠"),
    ("2021_monza", "2021 義大利大獎賽", "Verstappen 和 Hamilton 碰撞雙退，Ricciardo 爆冷奪冠"),
    ("2022_japan", "2022 日本大獎賽", "Verstappen 在暴雨中封王，但裁判判決引發爭議"),
    ("2023_qatar_sprint", "2023 卡達衝刺賽", "高溫下多名車手體力不支，Piastri 拿下首個衝刺冠軍"),
    ("2024_canada", "2024 加拿大大獎賽", "全場雨戰，Russell 精準判斷天氣變化時機奪冠"),
    ("2024_brazil", "2024 巴西大獎賽", "Verstappen 從 17 位起步逆轉奪冠，神級雨戰表演"),
]

print("\n═══ 5/7 經典賽事分析 ═══")
for rid, name, drama in CLASSIC_RACES:
    print(f"  Generating: {name}...")
    prompt = f"""你是 F1 歷史專家，用繁體中文寫一份經典賽事回顧。讓沒看過這場比賽的人也能感受到當時的緊張氣氛。

賽事：{name}
故事：{drama}

回應 JSON：
{{
  "story": "150字生動描述這場比賽的故事（要有畫面感）",
  "why_classic": "為什麼這場比賽值得記住",
  "turning_point": "比賽的轉折點",
  "winner_hero_moment": "冠軍最英雄的一刻",
  "data_point": "一個驚人的數據（圈速差/位置變化/進站時間等）",
  "lesson_for_betting": "這場比賽教會我們什麼預測技巧"
}}"""
    text = call_claude(prompt)
    save(f"classic:{rid}", "classic_race", name, clean_json(text))
    time.sleep(0.5)


# ════════════════════════════════════════════
# 6. 車手對決分析
# ════════════════════════════════════════════
RIVALRIES = [
    ("ver_nor", "Verstappen vs Norris", "冠軍爭奪戰：三冠王 vs 新世代最快"),
    ("lec_ham", "Leclerc vs Hamilton", "Ferrari 隊內戰：少主 vs 七冠傳奇"),
    ("nor_pia", "Norris vs Piastri", "McLaren 隊內戰：誰才是車隊一哥"),
    ("rus_ant", "Russell vs Antonelli", "Mercedes 隊內戰：經驗 vs 天賦"),
    ("ver_law", "Verstappen vs Lawson", "Red Bull 隊內戰：王者 vs 挑戰者"),
    ("alo_str", "Alonso vs Stroll", "Aston Martin：老將經驗 vs 二代目"),
    ("gas_doo", "Gasly vs Doohan", "Alpine 隊內戰：穩定輸出 vs 新秀衝勁"),
    ("tsu_had", "Tsunoda vs Hadjar", "Racing Bulls：鈴鹿武士 vs 法國新星"),
]

print("\n═══ 6/7 車手對決分析 ═══")
for rid, title, desc in RIVALRIES:
    print(f"  Generating: {title}...")
    prompt = f"""你是 F1 賽事分析專家，用繁體中文分析這組車手對決。語氣像體育評論員，有趣有深度。

對決：{title}
背景：{desc}

回應 JSON：
{{
  "narrative": "80字故事線描述（這組對決為什麼值得關注）",
  "driver_a_edge": "A 的優勢在哪",
  "driver_b_edge": "B 的優勢在哪",
  "head_to_head": "目前對戰紀錄預測",
  "key_battleground": "這組對決在什麼類型的賽道會最精彩",
  "prediction": "賽季結束誰會贏，為什麼",
  "betting_angle": "押 H2H 時要注意什麼"
}}"""
    text = call_claude(prompt)
    save(f"rivalry:{rid}", "rivalry", title, clean_json(text))
    time.sleep(0.5)


# ════════════════════════════════════════════
# 7. 賽季趨勢分析
# ════════════════════════════════════════════
TRENDS = [
    ("trend_mclaren_rise", "McLaren 的崛起", "從 2023 年中期開始的 McLaren 復興之路"),
    ("trend_ferrari_hamilton", "Hamilton 轉投 Ferrari", "F1 史上最大轉會，44號穿上紅色"),
    ("trend_newey_aston", "Newey 加入 Aston Martin", "傳奇設計師 Adrian Newey 離開 Red Bull"),
    ("trend_2026_regs", "2026 新規則", "引擎規則大改，電力系統比重增加"),
    ("trend_rookies", "2026 新秀大爆發", "Antonelli、Bearman、Hadjar、Bortoleto、Doohan 同時登場"),
    ("trend_verstappen_dominance", "Verstappen 王朝是否結束", "連續三年冠軍後面臨最大挑戰"),
    ("trend_sprint_format", "衝刺賽新制", "衝刺賽積分改制對冠軍爭奪的影響"),
    ("trend_budget_cap", "預算帽影響", "預算帽如何改變中場車隊的競爭力"),
]

print("\n═══ 7/7 賽季趨勢分析 ═══")
for tid, title, desc in TRENDS:
    print(f"  Generating: {title}...")
    prompt = f"""你是 F1 賽事分析專家和記者，用繁體中文寫一篇趨勢分析。讓新手也能理解這個議題的重要性。

主題：{title}
背景：{desc}

回應 JSON：
{{
  "headline": "吸引人的標題（20字內）",
  "summary": "100字摘要",
  "why_it_matters": "為什麼這件事很重要（對比賽結果的影響）",
  "data_evidence": "支持這個趨勢的數據或事實",
  "prediction_impact": "這個趨勢如何影響預測策略",
  "newbie_explainer": "30字給新手的白話解釋"
}}"""
    text = call_claude(prompt)
    save(f"trend:{tid}", "trend", title, clean_json(text))
    time.sleep(0.5)


# ════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════
conn.close()

print(f"""
═══════════════════════════════════
  批量生成完成！
  總呼叫次數：{generated}
  Input tokens：{total_input:,}
  Output tokens：{total_output:,}
  總 tokens：{total_input + total_output:,}
  預估成本：${total_input / 1000000 * 3 + total_output / 1000000 * 15:.4f}
═══════════════════════════════════
""")
