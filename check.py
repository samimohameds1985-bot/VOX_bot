
import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://egy.voxcinemas.com/"
TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
})

print("Connecting to VOX...")

response = session.get(URL, timeout=(15, 60))
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

movies = {}

for a in soup.select('a[href*="/movies/"]'):
    title_tag = a.find_previous(["h2", "h3", "h4"])

    name = (
        title_tag.get_text(strip=True)
        if title_tag
        else a.get("title") or a.get_text(strip=True)
    )

    if name and name.lower() != "view movie":
        link = urljoin(URL, a["href"])
        movies[link] = name

print("لقيت", len(movies), "فيلم")

if not movies:
    raise SystemExit("مفيش أفلام اتعرفت")

if os.path.exists(FILE):
    with open(FILE, encoding="utf-8") as f:
        seen = set(json.load(f))
else:
    seen = set()

new_movies = set(movies) - seen

print("الأفلام الجديدة:", len(new_movies))

for link in sorted(new_movies):
    message = f"🎬 فيلم جديد نزل على VOX!\n{movies[link]}\n{link}"

    response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=20
    )
    response.raise_for_status()

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(
        sorted(seen | set(movies)),
        f,
        ensure_ascii=False,
        indent=2
    )

print("VOX checker completed successfully!")
