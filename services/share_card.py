"""IG 戰績卡圖片生成 — PIL/Pillow"""
import io
from PIL import Image, ImageDraw, ImageFont
from services.usdclaw import get_balance
from database import get_db
from services.card_engine import determine_rarity
from config import RARITY


async def generate_share_card_image(username: str) -> io.BytesIO:
    balance = await get_balance(username)
    db = await get_db()
    try:
        row = await db.execute_fetchall(
            """SELECT COUNT(*), SUM(CASE WHEN result='won' THEN 1 ELSE 0 END)
               FROM bets WHERE username = ?""", (username,)
        )
        total_bets = row[0][0] if row else 0
        total_wins = row[0][1] or 0 if row else 0
    finally:
        await db.close()

    win_rate = round(total_wins / total_bets * 100, 1) if total_bets > 0 else 0
    rarity = determine_rarity({"total_bets": total_bets, "total_wins": total_wins})
    rarity_info = RARITY.get(rarity, RARITY["silverstone"])

    # Create image
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), "#0a0a0f")
    draw = ImageDraw.Draw(img)

    # Try to load font, fallback to default
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except:
        font_lg = ImageFont.load_default()
        font_md = font_lg
        font_sm = font_lg
        font_xs = font_lg

    gold = "#d4a843"
    white = "#f0f0f5"
    gray = "#888899"
    dark = "#1a1a25"

    # Background gradient effect (subtle)
    for y in range(0, 200):
        alpha = int(20 * (1 - y / 200))
        draw.rectangle([0, y, W, y + 1], fill=f"#{alpha:02x}{alpha:02x}{alpha + 10:02x}")

    # Top line
    draw.rectangle([0, 0, W, 4], fill=gold)

    # PITLANE logo
    draw.text((W // 2, 80), "PITLANE", fill=gold, font=font_lg, anchor="mm")

    # Divider
    draw.rectangle([100, 130, W - 100, 131], fill="#333")

    # Username
    draw.text((W // 2, 200), username, fill=white, font=font_md, anchor="mm")

    # Rarity badge
    rarity_colors = {"silverstone": "#a0a0b4", "monza": "#60a5fa", "suzuka": "#a855f7", "monaco": gold}
    rc = rarity_colors.get(rarity, gray)
    draw.rounded_rectangle([W // 2 - 120, 240, W // 2 + 120, 280], radius=20, fill=rc + "33", outline=rc)
    draw.text((W // 2, 260), rarity_info["name"], fill=rc, font=font_xs, anchor="mm")

    # Stats boxes
    stats = [
        ("USDClaw", f"{balance:,.0f}", gold),
        ("Total Bets", str(total_bets), white),
        ("Wins", str(total_wins), "#34d399"),
        ("Win Rate", f"{win_rate}%", "#3b82f6"),
    ]
    box_w = 200
    start_x = (W - box_w * 4 - 30 * 3) // 2
    y = 350
    for i, (label, value, color) in enumerate(stats):
        x = start_x + i * (box_w + 30)
        draw.rounded_rectangle([x, y, x + box_w, y + 120], radius=12, fill=dark, outline="#333")
        draw.text((x + box_w // 2, y + 45), value, fill=color, font=font_md, anchor="mm")
        draw.text((x + box_w // 2, y + 90), label, fill=gray, font=font_xs, anchor="mm")

    # Large center text
    draw.text((W // 2, 580), "F1 Prediction Master", fill=gray, font=font_sm, anchor="mm")

    # Decorative racing stripe
    draw.rectangle([0, 650, W, 654], fill=gold + "44")

    # Bottom section
    draw.text((W // 2, 750), "Join the race at", fill=gray, font=font_sm, anchor="mm")
    draw.text((W // 2, 810), "pitlane.gg", fill=gold, font=font_md, anchor="mm")

    # Bottom bar
    draw.rectangle([0, H - 4, W, H], fill=gold)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
