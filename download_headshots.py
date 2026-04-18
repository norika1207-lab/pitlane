"""One-shot downloader for driver headshots.

Primary source: F1 official CDN (media.formula1.com). Many older or non-current
drivers only return the ~4.5KB fallback silhouette there, so we fall back to
Wikipedia's REST summary endpoint which hosts Wikimedia Commons photos.

Accepts an image only if it's >6KB (a real photo, not a fallback silhouette).

Output: /opt/racing/static/assets/drivers/{name_acronym_lower}.png
"""
import asyncio
import sys
import urllib.parse
from pathlib import Path
import aiohttp

sys.path.insert(0, "/opt/racing")
from services import openf1

OUT_DIR = Path("/opt/racing/static/assets/drivers")
MIN_REAL_BYTES = 6000
UA = "PitLane/2.0 (contact abbychen981008@gmail.com)"

# Wikipedia page titles for drivers whose F1 CDN lookup fails.
# Keys are OpenF1 name_acronym. Use the exact Wikipedia page slug.
WIKIPEDIA_FALLBACK: dict[str, str] = {
    "VER": "Max_Verstappen",
    "HAM": "Lewis_Hamilton",
    "LEC": "Charles_Leclerc",
    "RUS": "George_Russell_(racing_driver)",
    "SAI": "Carlos_Sainz_Jr.",
    "PER": "Sergio_Pérez",
    "ALO": "Fernando_Alonso",
    "STR": "Lance_Stroll",
    "OCO": "Esteban_Ocon",
    "BOT": "Valtteri_Bottas",
    "ZHO": "Zhou_Guanyu",
    "TSU": "Yuki_Tsunoda",
    "HUL": "Nico_Hülkenberg",
    "MAG": "Kevin_Magnussen",
    "ALB": "Alexander_Albon",
    "BEA": "Oliver_Bearman",
    "ANT": "Andrea_Kimi_Antonelli",
    "BOR": "Gabriel_Bortoleto",
    "SAR": "Logan_Sargeant",
    "RIC": "Daniel_Ricciardo",
    "DEV": "Nyck_de_Vries",
    "MSC": "Mick_Schumacher",
    "VET": "Sebastian_Vettel",
    "RAI": "Kimi_Räikkönen",
    "GRO": "Romain_Grosjean",
    "GIO": "Antonio_Giovinazzi",
    "KVY": "Daniil_Kvyat",
    "MAZ": "Nikita_Mazepin",
    "LAT": "Nicholas_Latifi",
    "KUB": "Robert_Kubica",
}


def _f1_candidates(first: str, last: str) -> list[str]:
    if not first or not last:
        return []
    f3 = first[:3].upper()
    l3 = last[:3].upper()
    patterns = []
    for idv, letter in [(f"{l3}{f3}01", last[0].upper()),
                        (f"{f3}{l3}01", first[0].upper()),
                        (f"{l3}{f3}01", first[0].upper()),
                        (f"{f3}{l3}01", last[0].upper())]:
        url = (
            f"https://media.formula1.com/content/dam/fom-website/drivers/"
            f"{letter}/{idv}_{first}_{last}/{idv.lower()}.png.transform/1col/image.png"
        )
        if url not in patterns:
            patterns.append(url)
    return patterns


async def _try_download(session: aiohttp.ClientSession, url: str) -> bytes | None:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            body = await resp.read()
            if len(body) < MIN_REAL_BYTES:
                return None
            return body
    except Exception:
        return None


async def _wikipedia_image(session: aiohttp.ClientSession, page_title: str) -> bytes | None:
    """Fetch the original/thumbnail image from Wikipedia REST summary."""
    api = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(page_title)}"
    try:
        async with session.get(api, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
    except Exception:
        return None
    # Prefer thumbnail (already cropped) if available, fall back to original
    for key in ("thumbnail", "originalimage"):
        src = (data.get(key) or {}).get("source")
        if not src:
            continue
        body = await _try_download(session, src)
        if body:
            return body
    return None


async def _fetch_one(session: aiohttp.ClientSession, first: str, last: str, acronym: str) -> tuple[str, str]:
    # 1) Try F1 CDN
    for url in _f1_candidates(first, last):
        body = await _try_download(session, url)
        if body:
            (OUT_DIR / f"{acronym.lower()}.png").write_bytes(body)
            return acronym, f"F1   ({len(body):>6} B)"
    # 2) Wikipedia fallback
    wiki = WIKIPEDIA_FALLBACK.get(acronym)
    if wiki:
        body = await _wikipedia_image(session, wiki)
        if body:
            (OUT_DIR / f"{acronym.lower()}.png").write_bytes(body)
            return acronym, f"WIKI ({len(body):>6} B)"
    return acronym, "MISS"


async def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    drivers = await openf1.get_drivers()
    seen = set()
    unique = []
    for d in drivers or []:
        n = d.get("driver_number")
        if n in seen:
            continue
        seen.add(n)
        unique.append(d)
    print(f"{len(unique)} current-season drivers + historical fallback list")

    async with aiohttp.ClientSession(headers={"User-Agent": UA}) as session:
        tasks = []
        for d in unique:
            first = d.get("first_name") or ""
            last = d.get("last_name") or ""
            acronym = d.get("name_acronym") or ""
            if not acronym:
                continue
            tasks.append(_fetch_one(session, first, last, acronym))
        # Also download historical-only drivers from the Wikipedia map
        current_codes = {d.get("name_acronym") for d in unique}
        for code, title in WIKIPEDIA_FALLBACK.items():
            if code in current_codes:
                continue
            # Extract first/last from the wiki title for F1 CDN attempts
            clean = title.replace("_", " ")
            parts = clean.split()
            if len(parts) >= 2:
                tasks.append(_fetch_one(session, parts[0], parts[-1], code))

        results = await asyncio.gather(*tasks)

    got, miss = 0, 0
    for acronym, status in sorted(results):
        if status.startswith("MISS"):
            miss += 1
        else:
            got += 1
        print(f"  {acronym:4s}  {status}")
    print(f"\nDone: {got} downloaded, {miss} missing")


if __name__ == "__main__":
    asyncio.run(main())
