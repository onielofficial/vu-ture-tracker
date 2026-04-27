"""
whereisvulture.com → Discord Webhook
เรียก API ตรงๆ ที่ vulture-worker.arcadianglitch.workers.dev/location
"""

import requests
import re
import os
from datetime import datetime, timezone

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE")
API_URL = "https://vulture-worker.arcadianglitch.workers.dev/location"

# ─── LOGO / BRANDING ──────────────────────────────────────────────────────────
# 🖼️ วิธีเปลี่ยนภาพในอนาคต:
#   1. อัปโหลดรูปใหม่ไปที่ Discord channel ใดก็ได้
#   2. คลิกขวาที่รูป → "Copy Link" หรือ "Copy Media Link"
#   3. วาง URL นั้นมาแทนที่ค่า TEAM_LOGO_URL ด้านล่างนี้
#   4. หรือถ้าอัปโหลดไป Imgur / CDN อื่น ก็ใช้ URL ตรงๆ ได้เลย
#   หมายเหตุ: URL ของ Discord มี ?ex=... ที่หมดอายุได้
#             ถ้าภาพหาย ให้ re-upload แล้วเอา URL ใหม่มาใส่แทน

TEAM_LOGO_URL = "https://i.postimg.cc/VrrJBnK2/render2.png"

MITHRAS_ICON_URL = TEAM_LOGO_URL  # ใช้รูปเดียวกันเป็น thumbnail ด้วย
# ───────────────────────────────────────────────────────────────────────────────


def fetch_locations():
    """เรียก API โดยตรง ได้ JSON สะอาด ไม่ต้อง scrape"""
    resp = requests.get(API_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    locations = []
    for key in ["cop1", "cop2", "cop3", "cop4"]:
        if key not in data or not data[key]:
            continue
        raw = data[key]  # เช่น "Titan (Grid 153:121)"
        match = re.match(r"(.+?)\s*\(Grid\s*([\d:]+)\)", raw)
        if match:
            locations.append({
                "name": match.group(1).strip(),
                "grid": match.group(2).strip(),
            })
        else:
            locations.append({"name": key.upper(), "grid": raw})

    return locations, data.get("timestamp"), data.get("searching", False)


def build_discord_payload(locations, timestamp_iso, searching) -> dict:
    """สร้าง Discord embed payload พร้อม branding"""
    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    if timestamp_iso:
        try:
            dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
            last_seen = dt.strftime("%d %b %Y %H:%M UTC")
        except Exception:
            last_seen = timestamp_iso
    else:
        last_seen = now

    # ─── กรณีไม่มีข้อมูล ──────────────────────────────────────────────────────
    if not locations:
        return {
            "username": "Mithras Intel",
            "avatar_url": MITHRAS_ICON_URL,
            "embeds": [{
                "author": {
                    "name": "MITHRAS TEAM  •  Vulture Tracker",
                    "icon_url": MITHRAS_ICON_URL,
                },
                "title": "🔍 กำลังค้นหาตำแหน่ง..." if searching else "⚠️ ไม่พบข้อมูลตำแหน่ง",
                "description": (
                    "> Vulture กำลัง searching อยู่ครับ รอการอัปเดตครั้งถัดไป"
                    if searching else
                    "> ยังไม่มีข้อมูลในขณะนี้"
                ),
                "color": 0xF5C400 if searching else 0xFF4444,
                "thumbnail": {"url": TEAM_LOGO_URL},
                "footer": {
                    "text": f"Mithras Intel  •  {now}",
                    "icon_url": MITHRAS_ICON_URL,
                },
            }]
        }

    # ─── fields ตำแหน่ง ────────────────────────────────────────────────────────
    fields = []
    for loc in locations:
        fields.append({
            "name": f"📍 {loc['name']}",
            "value": f"```fix\nGrid {loc['grid']}```",
            "inline": True,
        })

    if searching:
        fields.append({
            "name": "🔍 สถานะ",
            "value": "> กำลัง searching หาตำแหน่งใหม่",
            "inline": False,
        })

    # spacer ให้ thumbnail ไม่ชนกับ fields (Discord quirk)
    fields.append({"name": "\u200b", "value": "\u200b", "inline": False})

    return {
        "username": "Mithras Intel",
        "avatar_url": MITHRAS_ICON_URL,
        "embeds": [{
            "author": {
                "name": "MITHRAS TEAM  •  Vulture Tracker",
                "icon_url": MITHRAS_ICON_URL,
            },
            "title": "🦅  Vulture — Current Locations",
            "url": "https://whereisvulture.com",
            "description": (
                "**Intel live** จาก [whereisvulture.com](https://whereisvulture.com)\n"
                "ตำแหน่งปัจจุบันของ Vulture ใน **Gray Zone Warfare**\n"
                "━━━━━━━━━━━━━━━━━━━━━━"
            ),
            "color": 0xF5C400,         # สีเหลือง Mithras
            "thumbnail": {"url": TEAM_LOGO_URL},   # โลโก้ทีมมุมขวา
            "fields": fields,
            "image": {"url": ""},      # ไม่ใส่ภาพใหญ่ (ลบบรรทัดนี้ถ้าอยากใส่ banner)
            "footer": {
                "text": f"Mithras Intel  •  Last Update: {last_seen}",
                "icon_url": MITHRAS_ICON_URL,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]
    }


def send_to_discord(payload: dict) -> bool:
    resp = requests.post(
        DISCORD_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if resp.status_code in (200, 204):
        print("✅ ส่ง Discord webhook สำเร็จ!")
        return True
    else:
        print(f"❌ Discord webhook error: {resp.status_code} — {resp.text}")
        return False


def main():
    print("🔍 กำลังดึงข้อมูลจาก API ...")
    try:
        locations, timestamp, searching = fetch_locations()
    except Exception as e:
        print(f"❌ ดึงข้อมูลไม่ได้: {e}")
        locations, timestamp, searching = [], None, False

    if locations:
        for loc in locations:
            print(f"   📍 {loc['name']}  Grid {loc['grid']}")
    else:
        print(f"   ⚠️  ไม่พบข้อมูล (searching={searching})")

    print("\n📤 กำลังส่งไป Discord ...")
    payload = build_discord_payload(locations, timestamp, searching)
    send_to_discord(payload)


if __name__ == "__main__":
    main()
