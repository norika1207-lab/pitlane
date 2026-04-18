"""Share card PNG — 1080×1080 F1-themed stat card for social share."""
import io
from PIL import Image, ImageDraw, ImageFont
from services.usdclaw import get_balance
from database import get_db
from services.card_engine import determine_rarity
from config import RARITY


# ── Palette ──────────────────────────────────────────────────────────
BG_TOP      = (18, 21, 32)
BG_BOT      = (8, 10, 16)
GOLD        = (212, 168, 67)
GOLD_DIM    = (130, 100, 38)
WHITE       = (240, 242, 248)
TEXT_DIM    = (168, 174, 196)
TEXT_MUTED  = (100, 106, 128)
LINE        = (38, 44, 62)
CARD_BG     = (22, 26, 38)
RED_F1      = (225, 6, 0)

RARITY_COLOR = {
    "silverstone": (160, 168, 184),
    "monza":       (96, 165, 250),
    "suzuka":      (168,  85, 247),
    "monaco":      (212, 168, 67),
}

# ── Font loader ──────────────────────────────────────────────────────
def _font(size: int, *, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    if mono:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    else:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _vertical_gradient(img: Image.Image, top: tuple, bot: tuple) -> None:
    """Paint vertical gradient onto existing image in-place."""
    w, h = img.size
    top_r, top_g, top_b = top
    bot_r, bot_g, bot_b = bot
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        r = int(top_r + (bot_r - top_r) * t)
        g = int(top_g + (bot_g - top_g) * t)
        b = int(top_b + (bot_b - top_b) * t)
        for x in range(w):
            px[x, y] = (r, g, b)


async def _collect_stats(username: str) -> dict:
    """Gather everything needed for the card from DB."""
    balance = await get_balance(username)
    db = await get_db()
    try:
        bets = await db.execute_fetchall(
            "SELECT COUNT(*), SUM(CASE WHEN result='won' THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN result='won' THEN payout-amount ELSE 0 END) "
            "FROM bets WHERE username=?", (username,))
        total_bets = bets[0][0] if bets else 0
        wins       = bets[0][1] or 0 if bets else 0
        profit     = bets[0][2] or 0 if bets else 0

        rpg = await db.execute_fetchall(
            "SELECT xp, win_streak, custom_title FROM user_rpg WHERE username=?", (username,))
        xp       = rpg[0][0] if rpg else 0
        streak   = rpg[0][1] if rpg else 0
        title    = rpg[0][2] if rpg and rpg[0][2] else None

        trophy_row = await db.execute_fetchall(
            "SELECT COUNT(*) FROM trophies WHERE username=?", (username,))
        trophies = trophy_row[0][0] if trophy_row else 0

        coll_row = await db.execute_fetchall(
            "SELECT COUNT(*) FROM halloffame_collection WHERE username=?", (username,))
        legends = coll_row[0][0] if coll_row else 0

        best_row = await db.execute_fetchall(
            "SELECT race_name, prediction, payout-amount FROM bets "
            "WHERE username=? AND result='won' ORDER BY payout-amount DESC LIMIT 1",
            (username,))
        best_bet = None
        if best_row:
            best_bet = {"race": best_row[0][0] or "—",
                        "pick": best_row[0][1] or "—",
                        "profit": best_row[0][2] or 0}
    finally:
        await db.close()

    win_rate = round(wins / total_bets * 100, 1) if total_bets else 0.0
    rarity = determine_rarity({"total_bets": total_bets, "total_wins": wins})

    return {
        "username":   username,
        "balance":    balance,
        "total_bets": total_bets,
        "wins":       wins,
        "win_rate":   win_rate,
        "profit":     profit,
        "xp":         xp,
        "streak":     streak,
        "trophies":   trophies,
        "legends":    legends,
        "title":      title,
        "best_bet":   best_bet,
        "rarity":     rarity,
        "rarity_info": RARITY.get(rarity, RARITY["silverstone"]),
        "rarity_color": RARITY_COLOR.get(rarity, RARITY_COLOR["silverstone"]),
    }


def _draw_stat_card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                    value: str, label: str, accent: tuple) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=CARD_BG, outline=LINE, width=1)
    draw.rectangle([x, y, x + 3, y + h], fill=accent)
    draw.text((x + w // 2, y + 42), value, fill=accent, font=_font(38, bold=True), anchor="mm")
    draw.text((x + w // 2, y + h - 26), label, fill=TEXT_MUTED, font=_font(16, bold=True), anchor="mm")


async def _current_round_label() -> str:
    """Best-effort 'ROUND NN' badge based on current race. Silent on failure."""
    try:
        from routes.races import current_race
        race = await current_race()
        rnd = race.get("round")
        if rnd:
            return f"ROUND {int(rnd):02d}"
    except Exception:
        pass
    return "SEASON 2026"


async def generate_share_card_image(username: str) -> io.BytesIO:
    s = await _collect_stats(username)
    round_label = await _current_round_label()

    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), BG_TOP)
    _vertical_gradient(img, BG_TOP, BG_BOT)
    draw = ImageDraw.Draw(img)

    # ── Racing stripes (top + bottom accent) ──────────────────────────
    draw.rectangle([0, 0, W, 6], fill=GOLD)
    draw.rectangle([0, 6, W, 8], fill=GOLD_DIM)
    draw.rectangle([0, H - 8, W, H - 6], fill=GOLD_DIM)
    draw.rectangle([0, H - 6, W, H], fill=GOLD)

    # Diagonal speed line (subtle)
    for i in range(0, 220, 12):
        draw.line([(W - 240 - i, 20), (W - 60 - i, 200)], fill=(34, 40, 58), width=3)

    # ── HEADER ────────────────────────────────────────────────────────
    # "PITLANE" wordmark, letter-spaced
    draw.text((60, 70), "P I T L A N E", fill=GOLD, font=_font(44, bold=True), anchor="lm")
    draw.text((60, 108), "F1 PREDICTION SEASON 2026", fill=TEXT_MUTED, font=_font(16, bold=True), anchor="lm")

    # Season badge (top-right) — dynamic round label
    badge_txt = round_label
    b_bbox = draw.textbbox((0, 0), badge_txt, font=_font(18, bold=True))
    b_w = (b_bbox[2] - b_bbox[0]) + 36
    bx = W - 60 - b_w
    draw.rounded_rectangle([bx, 50, bx + b_w, 100], radius=8, outline=GOLD, width=2,
                           fill=(GOLD[0]//10, GOLD[1]//10, GOLD[2]//10))
    draw.text((bx + b_w // 2, 75), badge_txt, fill=GOLD, font=_font(18, bold=True), anchor="mm")

    # Separator
    draw.rectangle([60, 150, W - 60, 151], fill=LINE)

    # ── HERO: Username + rarity ──────────────────────────────────────
    rc = s["rarity_color"]
    # Username (huge)
    username_display = s["username"][:18].upper()
    draw.text((60, 230), username_display, fill=WHITE, font=_font(72, bold=True), anchor="lm")

    # Custom title / rarity tier — in italic feel under the name
    tier_txt = (s["title"] or s["rarity_info"]["label"]).upper()
    draw.text((60, 290), tier_txt, fill=rc, font=_font(22, bold=True), anchor="lm")

    # Rarity pill (top right of hero row)
    pill_txt = s["rarity_info"]["name"].upper()
    pill_bbox = draw.textbbox((0, 0), pill_txt, font=_font(18, bold=True))
    pill_w = pill_bbox[2] - pill_bbox[0] + 40
    pill_x = W - 60 - pill_w
    pill_y = 210
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + 42], radius=21,
                           fill=(rc[0]//6, rc[1]//6, rc[2]//6), outline=rc, width=2)
    draw.text((pill_x + pill_w // 2, pill_y + 21), pill_txt, fill=rc, font=_font(18, bold=True), anchor="mm")

    # ── KPI ROW (4 cards) ─────────────────────────────────────────────
    box_w, box_h = 220, 130
    gap = 18
    total_w = box_w * 4 + gap * 3
    kx = (W - total_w) // 2
    ky = 380

    profit_val = f"+{s['profit']:,.0f}" if s["profit"] >= 0 else f"{s['profit']:,.0f}"
    kpis = [
        (f"{s['balance']:,.0f}",    "USDClaw",     GOLD),
        (str(s['total_bets']),       "Total Bets",  WHITE),
        (f"{s['win_rate']:.1f}%",    "Win Rate",    (52, 211, 153) if s['win_rate'] >= 50 else (251, 146, 60)),
        (profit_val,                 "Net Profit",  (52, 211, 153) if s['profit'] >= 0 else (248, 113, 113)),
    ]
    for i, (val, lab, acc) in enumerate(kpis):
        _draw_stat_card(draw, kx + i * (box_w + gap), ky, box_w, box_h, val, lab, acc)

    # ── CENTER STRIP: XP / Streak / Legends / Trophies ────────────────
    strip_y = 560
    draw.text((W // 2, strip_y), "◂ CAREER STATS ▸", fill=TEXT_MUTED, font=_font(14, bold=True), anchor="mm")

    stats_row_y = 620
    stat_labels = [
        (str(s["xp"]),       "XP"),
        (str(s["streak"]),   "STREAK"),
        (str(s["wins"]),     "WINS"),
        (str(s["trophies"]), "TROPHIES"),
        (str(s["legends"]),  "LEGENDS"),
    ]
    col_w = (W - 120) // len(stat_labels)
    for i, (val, lab) in enumerate(stat_labels):
        cx = 60 + col_w * i + col_w // 2
        draw.text((cx, stats_row_y),        val, fill=WHITE,      font=_font(40, bold=True), anchor="mm")
        draw.text((cx, stats_row_y + 42),   lab, fill=TEXT_MUTED, font=_font(14, bold=True), anchor="mm")
        if i < len(stat_labels) - 1:
            draw.rectangle([60 + col_w * (i + 1) - 1, stats_row_y - 22,
                            60 + col_w * (i + 1),     stats_row_y + 62], fill=LINE)

    # ── BEST BET HIGHLIGHT (if any) ───────────────────────────────────
    bb_y = 730
    draw.rounded_rectangle([60, bb_y, W - 60, bb_y + 140], radius=16, fill=CARD_BG, outline=LINE, width=1)
    draw.rectangle([60, bb_y, 64, bb_y + 140], fill=GOLD)
    draw.text((84, bb_y + 24), "★ BIGGEST WIN", fill=GOLD, font=_font(16, bold=True), anchor="lm")
    if s["best_bet"]:
        race = (s["best_bet"]["race"] or "")[:38]
        pick = (s["best_bet"]["pick"] or "")[:20]
        profit_str = f"+{s['best_bet']['profit']:,.0f} USDClaw"
        draw.text((84, bb_y + 62), race, fill=WHITE, font=_font(26, bold=True), anchor="lm")
        draw.text((84, bb_y + 100), f"Pick: {pick}", fill=TEXT_DIM, font=_font(18), anchor="lm")
        draw.text((W - 84, bb_y + 82), profit_str, fill=(52, 211, 153), font=_font(32, bold=True), anchor="rm")
    else:
        draw.text((84, bb_y + 78), "No completed wins yet — place your first bet!",
                  fill=TEXT_DIM, font=_font(22), anchor="lm")

    # ── CHECKERED FOOTER ─────────────────────────────────────────────
    foot_y = 910
    sq = 16
    for col in range(W // sq + 1):
        shade = WHITE if col % 2 == 0 else (24, 28, 40)
        draw.rectangle([col * sq, foot_y, col * sq + sq, foot_y + sq], fill=shade)

    # ── BOTTOM CTA ───────────────────────────────────────────────────
    draw.text((W // 2, foot_y + 50), "JOIN THE RACE", fill=TEXT_DIM, font=_font(14, bold=True), anchor="mm")
    draw.text((W // 2, foot_y + 90), "pitlane.gg", fill=GOLD, font=_font(46, bold=True), anchor="mm")
    draw.text((W // 2, foot_y + 130), "F1 PREDICTION · CARDS · LEGENDS", fill=TEXT_MUTED,
              font=_font(13, bold=True), anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
