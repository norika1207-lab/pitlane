"""賽事名稱中文對應表 — 從 circuit/country 對應到正式大獎賽名稱"""

CIRCUIT_TO_GP = {
    "Melbourne": "澳洲大獎賽",
    "Shanghai": "中國大獎賽",
    "Suzuka": "日本大獎賽",
    "Sakhir": "巴林大獎賽",
    "Jeddah": "沙烏地阿拉伯大獎賽",
    "Miami": "邁阿密大獎賽",
    "Imola": "艾米利亞-羅馬涅大獎賽",
    "Monaco": "摩納哥大獎賽",
    "Barcelona": "西班牙大獎賽",
    "Montréal": "加拿大大獎賽",
    "Montreal": "加拿大大獎賽",
    "Spielberg": "奧地利大獎賽",
    "Silverstone": "英國大獎賽",
    "Spa-Francorchamps": "比利時大獎賽",
    "Spa": "比利時大獎賽",
    "Budapest": "匈牙利大獎賽",
    "Hungaroring": "匈牙利大獎賽",
    "Zandvoort": "荷蘭大獎賽",
    "Monza": "義大利大獎賽",
    "Baku": "亞塞拜然大獎賽",
    "Marina Bay": "新加坡大獎賽",
    "Singapore": "新加坡大獎賽",
    "Austin": "美國大獎賽",
    "Mexico City": "墨西哥大獎賽",
    "São Paulo": "巴西大獎賽",
    "Sao Paulo": "巴西大獎賽",
    "Interlagos": "巴西大獎賽",
    "Las Vegas": "拉斯維加斯大獎賽",
    "Lusail": "卡達大獎賽",
    "Yas Marina": "阿布達比大獎賽",
    "Yas Island": "阿布達比大獎賽",
    "Portimão": "葡萄牙大獎賽",
    "Portimao": "葡萄牙大獎賽",
    "Istanbul": "土耳其大獎賽",
    "Nürburgring": "艾菲爾大獎賽",
    "Mugello": "托斯卡尼大獎賽",
    "Losail": "卡達大獎賽",
}

COUNTRY_TO_GP = {
    "Australia": "澳洲大獎賽",
    "China": "中國大獎賽",
    "Japan": "日本大獎賽",
    "Bahrain": "巴林大獎賽",
    "Saudi Arabia": "沙烏地阿拉伯大獎賽",
    "United States": "美國大獎賽",
    "Italy": "義大利大獎賽",
    "Monaco": "摩納哥大獎賽",
    "Spain": "西班牙大獎賽",
    "Canada": "加拿大大獎賽",
    "Austria": "奧地利大獎賽",
    "United Kingdom": "英國大獎賽",
    "Belgium": "比利時大獎賽",
    "Hungary": "匈牙利大獎賽",
    "Netherlands": "荷蘭大獎賽",
    "Azerbaijan": "亞塞拜然大獎賽",
    "Singapore": "新加坡大獎賽",
    "Mexico": "墨西哥大獎賽",
    "Brazil": "巴西大獎賽",
    "Qatar": "卡達大獎賽",
    "UAE": "阿布達比大獎賽",
    "United Arab Emirates": "阿布達比大獎賽",
    "Portugal": "葡萄牙大獎賽",
    "Turkey": "土耳其大獎賽",
}

# 賽道類型
CIRCUIT_TYPE = {
    "Melbourne": "street",
    "Shanghai": "technical",
    "Suzuka": "technical",
    "Sakhir": "high_speed",
    "Jeddah": "high_speed",
    "Miami": "street",
    "Imola": "technical",
    "Monaco": "street",
    "Barcelona": "technical",
    "Montréal": "street",
    "Montreal": "street",
    "Spielberg": "high_speed",
    "Silverstone": "high_speed",
    "Spa-Francorchamps": "high_speed",
    "Budapest": "technical",
    "Hungaroring": "technical",
    "Zandvoort": "technical",
    "Monza": "high_speed",
    "Baku": "street",
    "Marina Bay": "street",
    "Singapore": "street",
    "Austin": "technical",
    "Mexico City": "high_speed",
    "São Paulo": "technical",
    "Sao Paulo": "technical",
    "Las Vegas": "street",
    "Lusail": "high_speed",
    "Yas Marina": "technical",
}

CIRCUIT_TYPE_ZH = {
    "high_speed": "高速型賽道",
    "street": "街道賽道",
    "technical": "技術型賽道",
}


def get_race_name(circuit: str = "", country: str = "", meeting: str = "") -> str:
    """Get Chinese GP name from circuit/country."""
    if meeting and meeting != "?":
        return meeting
    name = CIRCUIT_TO_GP.get(circuit, "")
    if not name:
        name = COUNTRY_TO_GP.get(country, "")
    if not name:
        name = f"{country or circuit} 大獎賽"
    return name


def get_circuit_type(circuit: str) -> str:
    ct = CIRCUIT_TYPE.get(circuit, "technical")
    return CIRCUIT_TYPE_ZH.get(ct, "技術型賽道")


def get_circuit_type_raw(circuit: str) -> str:
    return CIRCUIT_TYPE.get(circuit, "technical")
