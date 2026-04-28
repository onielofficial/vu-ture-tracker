"""
whereisvulture.com → Discord Webhook
สไตล์ตรงตามภาพ ref เป๊ะ
"""

import requests
import re
import os
from datetime import datetime, timezone, timedelta

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE")
API_URL = "https://vulture-worker.arcadianglitch.workers.dev/location"

TEAM_LOGO_URL    = "https://i.postimg.cc/VrrJBnK2/render2.png"
MITHRAS_ICON_URL = TEAM_LOGO_URL

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
        m = re.match(r"(.+?)\s*\(Grid\s*([\d:]+)\)", raw)
        if m:
            locations.append({"name": m.group(1).strip(), "grid": m.group(2).strip()})
    return locations, data.get("timestamp"), data.get("searching", False)


def format_ts(ts):
    if not ts:
        return datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y %H:%M UTC")
    except Exception:
        return ts


def is_monday_thailand():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).weekday() == 0


def build_payload(locations, timestamp_iso, searching):
    last_seen = format_ts(timestamp_iso)
    now       = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    # ── ไม่มีข้อมูล ─────────────────────────────────────────────────────────
    if not locations:
        return {
            "username":   "MITHRAS INTEL",
            "avatar_url": MITHRAS_ICON_URL,
            "embeds": [{
                "author": {
                    "name":     "MITHRAS INTELLIGENCE NETWORK",
                    "icon_url": MITHRAS_ICON_URL,
                },
                "title": "🔍  VULTURE — SEARCHING" if searching else "⚠️  VULTURE — NO SIGNAL",
                "description": (
                    "```\nSTATUS   : SEARCHING\nUNIT     : VULTURE ACTUAL\nLOCATION : UNKNOWN\n```"
                    if searching else
                    "```\nSTATUS   : NO DATA\nSIGNAL   : LOST\n```"
                ),
                "color":     COLOR_ORANGE if searching else COLOR_RED,
                "thumbnail": {"url": TEAM_LOGO_URL},
                "footer": {
                    "text":     f"MITHRAS INTEL  •  {now}",
                    "icon_url": MITHRAS_ICON_URL,
                },
            }]
        }

    # ── มีตำแหน่ง ────────────────────────────────────────────────────────────
    fields = []
    for loc in locations:
        fields.append({
            "name":   f"🎯  {loc['name'].upper()}",
            "value":  f"```\nGRID : {loc['grid']}\n```",
            "inline": True,
        })
    fields.append({
        "name":   "📡  LAST CONFIRMED",
        "value":  f"```\n{last_seen}\n```",
        "inline": False,
    })

    return {
        "username":   "MITHRAS INTEL",
        "avatar_url": MITHRAS_ICON_URL,
        "embeds": [{
            "author": {
                "name":     "MITHRAS INTELLIGENCE NETWORK",
                "icon_url": MITHRAS_ICON_URL,
                "url":      "https://whereisvulture.com",
            },
            "title": "🦅  VULTURE ACTUAL — POSITION CONFIRMED",
            "description": (
                "```ansi\n\u001b[2;33m██ CLASSIFIED INTEL ██\u001b[0m\n```"
                "ตำแหน่งปัจจุบันของ **VULTURE** ใน Gray Zone Warfare"
            ),
            "color":     COLOR_GOLD,
            "thumbnail": {"url": TEAM_LOGO_URL},
            "fields":    fields,
            "footer": {
                "text":     "MITHRAS INTEL  •  whereisvulture.com",
                "icon_url": MITHRAS_ICON_URL,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }]
    }


def send(payload):
    r = requests.post(
        DISCORD_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if r.status_code in (200, 204):
        print("✅ ส่ง Discord webhook สำเร็จ!")
        return True
    print(f"❌ error: {r.status_code} — {r.text}")
    return False


def main():
    now_utc = datetime.now(timezone.utc)
    print(f"🕐 {now_utc.strftime('%A %d %b %Y %H:%M UTC')}")

    if False:
        print("📅 ไม่ใช่วันจันทร์ — keep-alive run เท่านั้น")
        return

    print("✅ วันจันทร์ — ส่ง Discord ...")
    try:
        locations, ts, searching = fetch_locations()
    except Exception as e:
        print(f"❌ {e}")
        locations, ts, searching = [], None, False

    for loc in locations:
        print(f"   📍 {loc['name']}  Grid {loc['grid']}")

    send(build_payload(locations, ts, searching))


if __name__ == "__main__":
    main()
