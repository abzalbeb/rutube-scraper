# main.py
import requests
from bs4 import BeautifulSoup
import json
import time
import re
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse

# ——— CORS uchun qo‘shimcha ———
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # yoki ["http://127.0.0.1:5500"] kabi faqat ma’lum domen
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app = FastAPI()
url = 'https://rutube.ru/channel/58919717/'
VIDEO_IDS_FILE = 'video_ids.json'

def duration_to_seconds(duration_str: str) -> int:
    parts = list(map(int, duration_str.split(':')))
    if len(parts) == 2:
        return parts[0]*60 + parts[1]
    elif len(parts) == 3:
        return parts[0]*3600 + parts[1]*60 + parts[2]
    return 0

def load_video_ids() -> list:
    try:
        with open(VIDEO_IDS_FILE, 'r') as f:
            data = f.read().strip()
            return json.loads(data) if data else []
    except FileNotFoundError:
        return []

def save_video_ids(ids: list):
    with open(VIDEO_IDS_FILE, 'w') as f:
        json.dump(ids, f)

def fetch_new_videos() -> list:
    existing = load_video_ids()
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    new = []

    for a in soup.find_all('a', href=True):
        if '/video/' not in a['href']:
            continue
        vid = a['href'].split('/video/')[-1].strip('/')
        if vid == "person/58919717":
            continue

        # duration
        duration_tag = a.find_next(string=re.compile(r'\d+:\d+'))
        if not duration_tag:
            continue
        seconds = duration_to_seconds(duration_tag.strip())
        if seconds > 90:
            continue

        if vid not in existing:
            existing.append(vid)
            new.append({'id': vid, 'duration': duration_tag.strip()})

    save_video_ids(existing)
    return new

@app.on_event("startup")
def startup_event():
    # Boshlang‘ich scraping — faylni yaratish uchun
    fetch_new_videos()

@app.get("/videos")
def get_all_videos():
    """Hozirgacha topilgan barcha video IDlarni qaytaradi."""
    ids = load_video_ids()
    return JSONResponse(content={"videos": ids})

@app.get("/videos/new")
def get_new_videos(background_tasks: BackgroundTasks):
    """
    Yangi videolarni aniqlaydi, ro‘yxatga qo‘shadi va qaytaradi.
    Front bu endpointni polling (masalan 10–60 sekundda bir marta) orqali chaqirishi mumkin.
    """
    new = fetch_new_videos()
    return JSONResponse(content={"new_videos": new})
