"""
whereisvulture.com → Discord Webhook
ดึงข้อมูลตำแหน่ง Titan & Nomad แล้วส่งไป Discord

วิธีใช้:
  pip install requests beautifulsoup4
  python vulture_discord_webhook.py

ตั้ง DISCORD_WEBHOOK_URL ใน environment variable หรือแก้ตรง config ด้านล่าง
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE")
SOURCE_URL = "https://whereisvulture.com"
# ───────────────────────────────────────────────────────────────────────────────


def fetch_locations() -> list[dict]:
    """
    ดึงข้อมูลตำแหน่งจาก whereisvulture.com
    คืนค่า list ของ dict แต่ละตัวแทน operator หนึ่งคน
    เช่น [{"name": "Titan", "grid": "153:121", "status": "ACTIVE", "type": "COP"}, ...]
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }

    resp = requests.get(SOURCE_URL, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    locations = []

    # ── วิธีที่ 1: ดึงจาก list items ที่มีข้อความ "Grid" ──────────────────────
    # ตัวอย่างจากภาพ: "• Titan (Grid 153:121)"
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if "Grid" in text:
            # แยก name และ grid
            # รูปแบบ: "• Titan (Grid 153:121)"
            import re
            match = re.search(r"([A-Za-z]+)\s*\(Grid\s*([\d:]+)\)", text)
            if match:
                locations.append({
                    "name": match.group(1),
                    "grid": match.group(2),
                })

    # ── วิธีที่ 2 (fallback): ดึงจาก card headers ──────────────────────────────
    if not locations:
        # หา card ที่มีชื่อ operator และ grid coordinates
        # โครงสร้างจากภาพ: header มีชื่อ + พิกัด เช่น "TITAN  153, 121"
        for card in soup.find_all(class_=lambda c: c and "card" in c.lower()):
            header = card.find(class_=lambda c: c and "header" in c.lower())
            if header:
                import re
                text = header.get_text(" ", strip=True)
                match = re.search(r"([A-Z]+)\s+([\d]+),\s*([\d]+)", text)
                if match:
                    locations.append({
                        "name": match.group(1).capitalize(),
                        "grid": f"{match.group(2)}:{match.group(3)}",
                    })

    return locations


def build_discord_payload(locations: list[dict]) -> dict:
    """สร้าง Discord embed payload"""

    now = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")

    if not locations:
        # ถ้าดึงข้อมูลไม่ได้
        return {
            "username": "Vulture Tracker",
            "avatar_url": "https://whereisvulture.com/favicon.ico",
            "embeds": [{
                "title": "⚠️ ไม่พบข้อมูลตำแหน่ง",
                "description": "ไม่สามารถดึงข้อมูลจาก whereisvulture.com ได้ในขณะนี้",
                "color": 0xFF4444,
                "footer": {"text": f"อัปเดตล่าสุด: {now}"},
            }]
        }

    # สร้าง fields สำหรับแต่ละ operator
    fields = []
    for loc in locations:
        fields.append({
            "name": f"📍 {loc['name']}",
            "value": f"```Grid {loc['grid']}```",
            "inline": True,
        })

    payload = {
        "username": "Vulture Tracker",
        "avatar_url": "https://whereisvulture.com/favicon.ico",
        "embeds": [{
            "title": "🦅 Vulture Current Locations",
            "url": SOURCE_URL,
            "description": "ตำแหน่งปัจจุบันของ Operator ใน Gray Zone Warfare",
            "color": 0xF5C400,   # สีเหลืองเหมือน UI ในเว็บ
            "fields": fields,
            "footer": {
                "text": f"📡 whereisvulture.com  •  อัปเดต: {now}",
            },
            "thumbnail": {
                "url": "https://whereisvulture.com/favicon.ico",
            },
        }]
    }

    return payload


def send_to_discord(payload: dict) -> bool:
    """ส่ง payload ไปยัง Discord webhook"""
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
    print("🔍 กำลังดึงข้อมูลจาก whereisvulture.com ...")

    try:
        locations = fetch_locations()
    except Exception as e:
        print(f"❌ ดึงข้อมูลไม่ได้: {e}")
        locations = []

    if locations:
        for loc in locations:
            print(f"   📍 {loc['name']}  Grid {loc['grid']}")
    else:
        print("   ⚠️  ไม่พบข้อมูลตำแหน่ง (จะส่ง error embed ไป Discord)")

    print("\n📤 กำลังส่งไป Discord ...")
    payload = build_discord_payload(locations)
    send_to_discord(payload)


# ── เรียกใช้โดยตรง ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()


# ── ตัวอย่างตั้ง Schedule (cron) ────────────────────────────────────────────────
# ถ้าต้องการส่งอัตโนมัติทุกชั่วโมง ให้เพิ่ม cron job:
#
#   crontab -e
#   0 * * * * /usr/bin/python3 /path/to/vulture_discord_webhook.py
#
# หรือใช้ schedule library ใน Python:
#
#   pip install schedule
#
#   import schedule, time
#   schedule.every().hour.do(main)
#   while True:
#       schedule.run_pending()
#       time.sleep(60)
