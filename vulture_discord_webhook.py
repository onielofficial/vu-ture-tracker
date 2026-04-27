"""
whereisvulture.com → Discord Webhook
ดึงข้อมูลตำแหน่ง Titan & Nomad แล้วส่งไป Discord
"""

import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE")
SOURCE_URL = "https://whereisvulture.com"
# ───────────────────────────────────────────────────────────────────────────────

# Headers จำลองเป็น browser จริง เพื่อหลบการบล็อก bot
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


def fetch_locations() -> list[dict]:
    """ดึงข้อมูลตำแหน่งจาก whereisvulture.com"""

    session = requests.Session()
    session.headers.update(HEADERS)

    resp = session.get(SOURCE_URL, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    locations = []

    # วิธีที่ 1: ดึงจาก list items รูปแบบ "• Titan (Grid 153:121)"
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if "Grid" in text:
            match = re.search(r"([A-Za-z]+)\s*\(Grid\s*([\d:,\s]+)\)", text)
            if match:
                grid = match.group(2).strip().replace(", ", ":").replace(",", ":")
                locations.append({
                    "name": match.group(1).capitalize(),
                    "grid": grid,
                })

    # วิธีที่ 2 (fallback): ดึงจาก card — รูปแบบ "TITAN  153, 121"
    if not locations:
        for card in soup.find_all(class_=lambda c: c and "card" in c.lower()):
            header = card.find(class_=lambda c: c and ("header" in c.lower() or "title" in c.lower()))
            if header:
                text = header.get_text(" ", strip=True)
                match = re.search(r"([A-Z][a-zA-Z]+)\s+([\d]+)[,\s]+([\d]+)", text)
                if match:
                    locations.append({
                        "name": match.group(1).capitalize(),
                        "grid": f"{match.group(2)}:{match.group(3)}",
                    })

    # วิธีที่ 3 (fallback): ค้นหาจาก text ทั้งหน้า
    if not locations:
        full_text = soup.get_text()
        for match in re.finditer(r"(Titan|Nomad|TITAN|NOMAD)\s*[\(\[]?Grid\s*([\d]+)[:\s,]+([\d]+)", full_text, re.IGNORECASE):
            locations.append({
                "name": match.group(1).capitalize(),
                "grid": f"{match.group(2)}:{match.group(3)}",
            })

    # ลบ duplicate
    seen = set()
    unique = []
    for loc in locations:
        key = loc["name"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(loc)

    return unique


def build_discord_payload(locations: list[dict]) -> dict:
    """สร้าง Discord embed payload"""
    now = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")

    if not locations:
        return {
            "username": "Vulture Tracker",
            "embeds": [{
                "title": "⚠️ ไม่พบข้อมูลตำแหน่ง",
                "description": (
                    "ไม่สามารถดึงข้อมูลจาก whereisvulture.com ได้\n"
                    "อาจเป็นเพราะเว็บยังไม่อัปเดต หรือโครงสร้างเว็บเปลี่ยนไป"
                ),
                "color": 0xFF4444,
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

    return {
        "username": "Vulture Tracker",
        "embeds": [{
            "title": "🦅 Vulture Current Locations",
            "url": SOURCE_URL,
            "description": "ตำแหน่งปัจจุบันของ Operator ใน Gray Zone Warfare",
            "color": 0xF5C400,
            "fields": fields,
            "footer": {"text": f"📡 whereisvulture.com  •  อัปเดต: {now}"},
        }]
    }


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
        print("   ⚠️  ไม่พบข้อมูลตำแหน่ง")

    print("\n📤 กำลังส่งไป Discord ...")
    payload = build_discord_payload(locations)
    send_to_discord(payload)


if __name__ == "__main__":
    main()
