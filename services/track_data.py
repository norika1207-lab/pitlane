"""賽道完整資料庫"""

TRACKS = {
    "Jeddah": {
        "name_zh": "吉達街道賽道", "name_en": "Jeddah Corniche Circuit",
        "country": "沙烏地阿拉伯", "type": "street", "difficulty": 8,
        "overtaking": 3, "pit_importance": 7, "wet_chaos": 9, "night_race": True,
        "characteristics": ["全球最快街道賽道，平均時速 250km+", "護牆超近，安全車出現機率極高",
                           "夜間賽事，輪胎溫度管理更難", "直線極速優先，下壓力設定低"],
        "strategy": "一停策略為主，軟胎起跑", "weather_avg": {"temp": 28, "rain_chance": 5},
    },
    "Monaco": {
        "name_zh": "摩納哥市街賽道", "name_en": "Circuit de Monaco",
        "country": "摩納哥", "type": "street", "difficulty": 10,
        "overtaking": 1, "pit_importance": 9, "wet_chaos": 10, "night_race": False,
        "characteristics": ["排位賽決定八成結果，超車幾乎不可能", "護牆距離最近，心理壓力最大",
                           "進站時機是唯一逆轉機會", "雨戰最混亂，黑馬最容易出現"],
        "strategy": "排位賽全力拼，正賽保住位置",
    },
    "Melbourne": {
        "name_zh": "亞伯特公園賽道", "name_en": "Albert Park Circuit",
        "country": "澳洲", "type": "street", "difficulty": 6,
        "overtaking": 5, "pit_importance": 6, "wet_chaos": 7, "night_race": False,
        "characteristics": ["賽季開幕站，賽車可靠度尚未驗證", "公園內半永久賽道，路面顛簸",
                           "DRS 區多，超車機會不少", "經常有安全車出現"],
        "strategy": "一停或二停皆可，視輪胎衰退決定",
    },
    "Shanghai": {
        "name_zh": "上海國際賽道", "name_en": "Shanghai International Circuit",
        "country": "中國", "type": "technical", "difficulty": 7,
        "overtaking": 6, "pit_importance": 7, "wet_chaos": 6, "night_race": False,
        "characteristics": ["超長直線搭配技術型彎道", "輪胎衰退嚴重，策略極其重要",
                           "二停策略經常有奇效", "風大，空力穩定性是關鍵"],
        "strategy": "二停策略可能有優勢",
    },
    "Suzuka": {
        "name_zh": "鈴鹿賽道", "name_en": "Suzuka International Racing Course",
        "country": "日本", "type": "technical", "difficulty": 9,
        "overtaking": 4, "pit_importance": 7, "wet_chaos": 8, "night_race": False,
        "characteristics": ["八字形賽道，唯一的立交設計", "S 彎是全 F1 最考驗下壓力的路段",
                           "130R 高速彎需要極大勇氣", "車手圈速差距最容易拉開的賽道"],
        "strategy": "一停為主，但 130R 輪胎磨耗需注意",
    },
    "Sakhir": {
        "name_zh": "巴林國際賽道", "name_en": "Bahrain International Circuit",
        "country": "巴林", "type": "high_speed", "difficulty": 5,
        "overtaking": 7, "pit_importance": 6, "wet_chaos": 3, "night_race": True,
        "characteristics": ["沙漠夜間賽事，沙塵影響抓地力", "多個急煞車區，超車機會多",
                           "輪胎過熱是最大挑戰", "後輪驅動力需求高"],
        "strategy": "二停策略在高溫下可能更好",
    },
    "Silverstone": {
        "name_zh": "銀石賽道", "name_en": "Silverstone Circuit",
        "country": "英國", "type": "high_speed", "difficulty": 8,
        "overtaking": 5, "pit_importance": 7, "wet_chaos": 9, "night_race": False,
        "characteristics": ["F1 的家鄉，高速彎道之王", "Copse 和 Maggots-Becketts 是全場最快彎組",
                           "英國天氣不可預測，隨時可能下雨", "Hamilton 主場優勢明顯"],
        "strategy": "一停為主，但英國天氣可能打亂計畫",
    },
    "Monza": {
        "name_zh": "蒙扎國家賽道", "name_en": "Autodromo Nazionale Monza",
        "country": "義大利", "type": "high_speed", "difficulty": 4,
        "overtaking": 8, "pit_importance": 5, "wet_chaos": 5, "night_race": False,
        "characteristics": ["全年最快賽道，平均時速超過 260km/h", "低下壓力設定，直線速度決定一切",
                           "尾流效應明顯，DRS 超車容易", "引擎馬力差距在這裡被放大"],
        "strategy": "一停策略，尾流戰術很重要",
    },
    "Spa-Francorchamps": {
        "name_zh": "斯帕賽道", "name_en": "Circuit de Spa-Francorchamps",
        "country": "比利時", "type": "high_speed", "difficulty": 9,
        "overtaking": 6, "pit_importance": 7, "wet_chaos": 10, "night_race": False,
        "characteristics": ["Eau Rouge-Raidillon 是 F1 最著名彎道組合", "賽道長 7km，天氣可能一半晴一半雨",
                           "海拔變化大，空力設定需要妥協", "安全車出現率極高"],
        "strategy": "天氣是最大變數，需要靈活應變",
    },
    "Miami": {
        "name_zh": "邁阿密國際賽道", "name_en": "Miami International Autodrome",
        "country": "美國", "type": "street", "difficulty": 6,
        "overtaking": 5, "pit_importance": 6, "wet_chaos": 7, "night_race": False,
        "characteristics": ["南佛羅里達高溫高濕環境", "路面顛簸，輪胎磨耗快",
                           "硬體圍牆多，碰撞出安全車機率高", "觀光賽事氣氛，但競爭激烈"],
        "strategy": "一停為主，注意高溫下的輪胎退化",
    },
    "Baku": {
        "name_zh": "巴庫市街賽道", "name_en": "Baku City Circuit",
        "country": "亞塞拜然", "type": "street", "difficulty": 8,
        "overtaking": 7, "pit_importance": 6, "wet_chaos": 8, "night_race": False,
        "characteristics": ["超長直線 + 超窄老城區彎道", "爆胎率全年最高，護牆超近",
                           "安全車出現率歷史上超過 80%", "逆轉劇情最常發生的賽道"],
        "strategy": "保守開局，等安全車出現後再出手",
    },
    "Marina Bay": {
        "name_zh": "濱海灣街道賽道", "name_en": "Marina Bay Street Circuit",
        "country": "新加坡", "type": "street", "difficulty": 9,
        "overtaking": 2, "pit_importance": 8, "wet_chaos": 9, "night_race": True,
        "characteristics": ["亞洲夜間賽事，濕熱環境極度考驗體能", "23 個彎道，全場最多",
                           "幾乎不可能超車，排位和進站決定一切", "車手體能極限賽道"],
        "strategy": "排位決勝，正賽靠進站策略",
    },
    "Lusail": {
        "name_zh": "盧賽爾國際賽道", "name_en": "Lusail International Circuit",
        "country": "卡達", "type": "high_speed", "difficulty": 6,
        "overtaking": 6, "pit_importance": 6, "wet_chaos": 2, "night_race": True,
        "characteristics": ["沙漠夜間賽，幾乎不會下雨", "高速連續彎道考驗下壓力",
                           "輪胎磨耗嚴重，可能需要二停", "路緣石很激進"],
        "strategy": "二停策略可能是最佳選擇",
    },
    "Yas Marina": {
        "name_zh": "亞斯碼頭賽道", "name_en": "Yas Marina Circuit",
        "country": "阿布達比", "type": "technical", "difficulty": 5,
        "overtaking": 5, "pit_importance": 6, "wet_chaos": 2, "night_race": True,
        "characteristics": ["賽季收官站，冠軍可能在這裡決定", "黃昏到夜晚賽事，溫度變化大",
                           "2021 改建後超車機會增加", "輪胎策略比較直接"],
        "strategy": "一停策略為主",
    },
}


def get_track(circuit: str) -> dict:
    """取得賽道資料"""
    return TRACKS.get(circuit, {
        "name_zh": f"{circuit} 賽道", "type": "technical", "difficulty": 5,
        "overtaking": 5, "pit_importance": 5, "wet_chaos": 5, "night_race": False,
        "characteristics": ["資料建置中"], "strategy": "一停策略為主",
    })


def get_all_tracks() -> dict:
    return TRACKS
