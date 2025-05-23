from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

import requests
from bs4 import BeautifulSoup
import json
import re

# Config
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        default = {"channel_url": "https://rutube.ru/channel/58919717/"}
        with open('config.json', 'w') as f:
            json.dump(default, f)
        return default

def save_config(config: dict):
    with open('config.json', 'w') as f:
        json.dump(config, f)

# Video IDs
VIDEO_IDS_FILE = 'video_ids.json'

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

# Helpers
def duration_to_seconds(duration_str: str) -> int:
    parts = list(map(int, duration_str.split(':')))
    if len(parts) == 2:
        return parts[0]*60 + parts[1]
    elif len(parts) == 3:
        return parts[0]*3600 + parts[1]*60 + parts[2]
    return 0

def get_channel_url():
    return load_config().get('channel_url')

# 🔁 Barcha yaroqli videolarni topish
def fetch_all_valid_videos() -> list:
    url = get_channel_url()
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kanal yuklanmadi: {str(e)}")

    soup = BeautifulSoup(resp.text, 'html.parser')
    valid_ids = []

    for a in soup.find_all('a', href=True):
        if '/video/' not in a['href']:
            continue
        vid = a['href'].split('/video/')[-1].strip('/')
        if vid.startswith('person/'):
            continue

        duration_tag = a.find_next(string=re.compile(r'\d+:\d+'))
        if not duration_tag:
            continue
        seconds = duration_to_seconds(duration_tag.strip())
        if seconds > 90:
            continue

        if vid not in valid_ids:
            valid_ids.append(vid)

    save_video_ids(valid_ids)
    return valid_ids

# App setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChannelUpdate(BaseModel):
    channel_url: HttpUrl

# API Endpoints
@app.get("/videos")
def get_all_videos(proxy: bool = Query(False, description="If true, fetch latest videos from channel")):
    if proxy:
        try:
            ids = fetch_all_valid_videos()
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"Fetch xatolik: {str(e)}"})
    else:
        ids = load_video_ids()

    return JSONResponse(content={"videos": ids})

@app.get("/channel")
def get_channel():
    config = load_config()
    return JSONResponse(content={"channel_url": config['channel_url']})

@app.post("/channel")
def update_channel(update: ChannelUpdate):
    config = {"channel_url": str(update.channel_url)}
    save_config(config)

    try:
        fetched_ids = fetch_all_valid_videos()
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "error": f"Kanal yangilandi, ammo videolarni olishda xatolik: {str(e)}"
        })

    return JSONResponse(content={
        "message": "Channel URL updated",
        "channel_url": config['channel_url'],
        "fetched_video_ids": fetched_ids
    })
