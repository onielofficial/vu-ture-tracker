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
# ───────────────────────────────────────────────────────────────────────────────


def fetch_locations() -> list[dict]:
    """เรียก API โดยตรง ได้ JSON สะอาด ไม่ต้อง scrape"""
    resp = requests.get(API_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # data มีหน้าตาแบบนี้:
    # {
    #   "cop1": "Titan (Grid 153:121)",
    #   "cop2": "Nomad (Grid 189:157)",
    #   "timestamp": "2026-04-21T00:58:03.150Z",
    #   "searching": false
    # }

    locations = []
    for key in ["cop1", "cop2", "cop3", "cop4"]:  # รองรับถ้าเพิ่ม cop ในอนาคต
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
            # ถ้ารูปแบบต่างออกไป เก็บ raw ไว้ก่อน
            locations.append({"name": key.upper(), "grid": raw})

    return locations, data.get("timestamp"), data.get("searching", False)


def build_discord_payload(locations, timestamp_iso, searching) -> dict:
    """สร้าง Discord embed payload"""
    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    # แปลง timestamp จาก API เป็นวันที่อ่านง่าย
    if timestamp_iso:
        try:
            dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
            last_seen = dt.strftime("%d %b %Y %H:%M UTC")
        except Exception:
            last_seen = timestamp_iso
    else:
        last_seen = now

    if not locations:
        return {
            "username": "Vulture Tracker",
            "embeds": [{
                "title": "🔍 กำลังค้นหาตำแหน่ง" if searching else "⚠️ ไม่พบข้อมูลตำแหน่ง",
                "description": "Vulture กำลัง searching อยู่ครับ รอการอัปเดตครั้งถัดไป" if searching else "ยังไม่มีข้อมูลในขณะนี้",
                "color": 0xF5C400 if searching else 0xFF4444,
                "footer": {"text": f"อัปเดตล่าสุด: {now}"},
            }]
        }

    fields = []
    for loc in locations:
        fields.append({
            "name": f"📍 {loc['name']}",
            "value": f"```Grid {loc['grid']}```",
            "inline": True,
        })

    # เพิ่ม field แสดงสถานะ searching
    if searching:
        fields.append({
            "name": "🔍 สถานะ",
            "value": "กำลัง searching หาตำแหน่งใหม่",
            "inline": False,
        })

    return {
        "username": "Vulture Tracker",
        "embeds": [{
            "title": "🦅 Vulture Current Locations",
            "url": "https://whereisvulture.com",
            "description": "ตำแหน่งปัจจุบันของ Operator ใน Gray Zone Warfare",
            "color": 0xF5C400,
            "fields": fields,
            "footer": {"text": f"📡 ข้อมูล ณ {last_seen}"},
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
