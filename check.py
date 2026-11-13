
import os
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://egy.voxcinemas.com"
URL = BASE_URL + "/movies/whatson"

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

FILE = "seen.json"

headers = {
    "User-Agent": "Mozilla/5.0"
}


from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()

retry = Retry(
    total=4,
    connect=4,
    read=4,
    backoff_factor=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

session.mount("https://", HTTPAdapter(max_retries=retry))

response = session.get(
    URL,
    headers=headers,
    timeout=(15, 90)
)

response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

movies = {}

for a in soup.select('a[href]'):
    href = urljoin(BASE_URL, a["href"])
    path = urlparse(href).path.rstrip("/")

    if not path.startswith("/movies/"):
        continue

    if path in ("/movies/whatson", "/movies/comingsoon"):
        continue

    name = a.get_text(" ", strip=True)

    if not name:
        name = a.get("title", "")

    if not name:
        img = a.find("img")
        if img:
            name = img.get("alt", "")

    if name and name.lower() != "showtimes":
        movies[href] = name

if not movies:
    raise RuntimeError("No movies found. Check website structure.")

print("Found:", len(movies), "movies")

if os.path.exists(FILE):
    with open(FILE, encoding="utf-8") as f:
        seen = json.load(f)
else:
    seen = {}

if not isinstance(seen, dict):
    seen = {}

# First run: save existing movies without sending old notifications
if not seen:
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)

    print("Initial movie list saved.")
    raise SystemExit(0)

new_movies = {
    link: name
    for link, name in movies.items()
    if link not in seen
}

for link, name in new_movies.items():
    message = f"🎬 فيلم جديد على VOX!\n\n{name}\n{link}"

    for attempt in range(3):
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={
                    "chat_id": CHAT_ID,
                    "text": message
                },
                timeout=30
            )
            r.raise_for_status()

            result = r.json()
            if not result.get("ok"):
                raise RuntimeError("Telegram rejected the message")

            print("Sent:", name)
            break

        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(5)

seen.update(movies)

with open(FILE, "w", encoding="utf-8") as f:
    json.dump(seen, f, ensure_ascii=False, indent=2)

print("Finished successfully!")
