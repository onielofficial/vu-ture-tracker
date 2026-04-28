"""
whereisvulture.com → Discord Webhook
สไตล์ CLASSIFIED INTEL + โลโก้ทีม Mithras
"""

import requests
import re
import os
from datetime import datetime, timezone, timedelta

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE")
API_URL = "https://vulture-worker.arcadianglitch.workers.dev/location"

# โลโก้ทีม (แก้ URL ตรงนี้ถ้าเปลี่ยนรูปในอนาคต)
TEAM_LOGO_URL = "https://i.postimg.cc/VrrJBnK2/render2.png"
MITHRAS_ICON_URL = TEAM_LOGO_URL

# สีธีม
COLOR_GOLD   = 0xD4A017
COLOR_RED    = 0xC0392B
COLOR_ORANGE = 0xE67E22
# ───────────────────────────────────────────────────────────────────────────────


def fetch_locations():
    resp = requests.get(API_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    locations = []
    for key in ["cop1", "cop2", "cop3", "cop4"]:
        if key not in data or not data[key]:
            continue
        raw = data[key]
        match = re.match(r"(.+?)\s*\(Grid\s*([\d:]+)\)", raw)
        if match:
            locations.append({
                "name": match.group(1).strip(),
                "grid": match.group(2).strip(),
            })
    return locations, data.get("timestamp"), data.get("searching", False)


def format_timestamp(ts):
    if not ts:
        return datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y %H:%M UTC")
    except Exception:
        return ts


def is_monday_thailand():
    now_thai = datetime.now(timezone.utc) + timedelta(hours=7)
    return now_thai.weekday() == 0


def build_discord_payload(locations, timestamp_iso, searching):
    last_seen = format_timestamp(timestamp_iso)
    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    # ── ไม่มีข้อมูล / searching ─────────────────────────────────────────────
    if not locations:
        return {
            "username": "MITHRAS INTEL",
            "avatar_url": MITHRAS_ICON_URL,
            "embeds": [{
                "author": {
                    "name": "MITHRAS INTELLIGENCE NETWORK",
                    "icon_url": MITHRAS_ICON_URL,
                },
                "title": "🔍  VULTURE — SEARCHING" if searching else "⚠️  VULTURE — NO SIGNAL",
                "description": (
                    "```\nSTATUS   : SEARCHING\nUNIT     : VULTURE ACTUAL\nLOCATION : UNKNOWN\n```"
                    if searching else
                    "```\nSTATUS   : NO DATA\nSIGNAL   : LOST\n```"
                ),
                "color": COLOR_ORANGE if searching else COLOR_RED,
                "thumbnail": {"url": TEAM_LOGO_URL},
                "footer": {
                    "text": f"MITHRAS INTEL  •  {now}",
                    "icon_url": MITHRAS_ICON_URL,
                },
            }]
        }

    # ── มีตำแหน่ง ────────────────────────────────────────────────────────────
    fields = []
    for loc in locations:
        fields.append({
            "name": f"🎯  {loc['name'].upper()}",
            "value": f"```\nGRID : {loc['grid']}\n```",
            "inline": True,
        })

    fields.append({
        "name": "📡  LAST CONFIRMED",
        "value": f"```\n{last_seen}\n```",
        "inline": False,
    })

    return {
        "username": "MITHRAS INTEL",
        "avatar_url": MITHRAS_ICON_URL,
        "embeds": [{
            "author": {
                "name": "MITHRAS INTELLIGENCE NETWORK",
                "icon_url": MITHRAS_ICON_URL,
                "url": "https://whereisvulture.com",
            },
            "title": "🦅  VULTURE ACTUAL — POSITION CONFIRMED",
            "description": (
                "```ansi\n\u001b[2;33m██ CLASSIFIED INTEL ██\u001b[0m\n```"
                "ตำแหน่งปัจจุบันของ **VULTURE** ใน Gray Zone Warfare"
            ),
            "color": COLOR_GOLD,
            "thumbnail": {"url": TEAM_LOGO_URL},
            "fields": fields,
            "footer": {
                "text": "MITHRAS INTEL  •  whereisvulture.com",
                "icon_url": MITHRAS_ICON_URL,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]
    }


def send_to_discord(payload):
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
    now_utc = datetime.now(timezone.utc)
    print(f"🕐 เวลาปัจจุบัน: {now_utc.strftime('%A %d %b %Y %H:%M UTC')}")

    if not is_monday_thailand():
        print("📅 วันนี้ไม่ใช่วันจันทร์ — ข้ามการส่ง Discord (keep-alive run)")
        print("✅ workflow รันสำเร็จ repo ยังคง active")
        return

    print("✅ วันจันทร์ — เริ่มดึงข้อมูลและส่ง Discord ...")
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
