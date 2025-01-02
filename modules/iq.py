import http.cookiejar
import re
import os
import json
import signal
import shutil
import requests
import cloudscraper
import subprocess
from modules.cookies import load_cookies
from modules.logging import setup_logging
from bs4 import BeautifulSoup

logger = setup_logging("IQ")

# ===================================================================================================================================================== #

def create_scraper():
    """Create a cloudscraper instance."""
    return cloudscraper.create_scraper()

# ===================================================================================================================================================== #

def parse_json_from_html(html, element_id):
    """Parse JSON data embedded in a script tag from HTML."""
    try:
        soup = BeautifulSoup(html, "lxml")
        script_content = soup.find("script", {"id": element_id}).text
        return json.loads(script_content)
    except Exception as e:
        logger.error(f"Error parsing JSON from HTML: {e}")
        return None

# ===================================================================================================================================================== #

def extract_data(html, key_path):
    """Extract nested data from parsed JSON using a key path."""
    data = parse_json_from_html(html, "__NEXT_DATA__")
    try:
        for key in key_path:
            data = data[key]
        return data
    except KeyError as e:
        logger.error(f"Key not found in JSON: {e} skipping...")
        return None

# ===================================================================================================================================================== #

def get_video_m3u8(html):
    """Extract and save the m3u8 link from HTML."""
    videos = extract_data(html, ["props", "initialProps", "pageProps", "prePlayerData", "dash", "data", "program", "video"])
    if videos:
        for video in videos:
            if "m3u8" in video:
                with open("temp.m3u8", "w") as file:
                    file.write(video["m3u8"])
                logger.info("Saved m3u8 file to temp.m3u8")
                return video["m3u8"]
    logger.warning("No m3u8 link found.")
    return None

# ===================================================================================================================================================== #

def fetch_html(url, res, lang, cookies):
    """Fetch HTML content from the URL with updated cookies."""
    cookies = load_cookies("cookies/cookies.txt")
    cookies.update({'lang': lang, 'QiyiPlayerBID': str(res)})
    scraper = create_scraper()
    try:
        response = scraper.get(url, cookies=cookies)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.error(f"Error fetching URL: {e}")
        exit(1)
        
# ===================================================================================================================================================== #

def get_album_id(base_html):
    next_data = json.loads(BeautifulSoup(base_html, features="lxml").find("script", {"id": "__NEXT_DATA__"}).text)
    return str(next_data['props']['initialState']['album']['videoAlbumInfo']['albumId'])

# ===================================================================================================================================================== #

def get_episodes(html, lang):
    album_id = get_album_id(html)
    if not album_id:
        return []
    
    url = f"https://pcw-api.iq.com/api/v2/episodeListSource/{album_id}"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "x-forwarded-for": "82.102.19.66"
    }
    params = {
        "platformId": "3",
        "modeCode": "my",
        "langCode": lang,
        "startOrder": "0",
        "endOrder": "10000"
    }
    scraper = create_scraper()
    try:
        response = scraper.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return [f"https://www.iq.com/play/{e['playLocSuffix']}" for e in data.get("data", {}).get("epg", []) if "playLocSuffix" in e]
    except Exception as e:
        logger.error(f"Failed to retrieve episodes: {e}")
        return []

# ===================================================================================================================================================== #

def get_series_title(base_html):
    try:
        return BeautifulSoup(base_html, features="lxml").find("span", {"class": "intl-album-title-word-wrap"}).find('span').text
    except Exception as e:
        logger.error(f'Failed to get series title {e}')

# ===================================================================================================================================================== #

def get_album_id(html):
    """Extract album ID from HTML."""
    return extract_data(html, ["props", "initialState", "album", "videoAlbumInfo", "albumId"])

# ===================================================================================================================================================== #

def get_title(html):
    """Extract title from HTML."""
    try:
        return BeautifulSoup(html, "lxml").find("p", {"class": "intl-play-title"}).text
    except Exception:
        logger.error("Failed to get title (wrong URL?)")
        exit(1)


# ===================================================================================================================================================== #

def slugify(value):
    """Slugify a string for safe file naming."""
    value = str(value)
    value = re.sub(r"[^\w\s-]", "", value)
    return re.sub(r"[-\s]+", ".", value).strip("-_")

# ===================================================================================================================================================== #

def download_media(foldername, filename):
    foldername, filename = slugify(foldername), slugify(filename)
    os.makedirs(f"Downloads/{foldername}", exist_ok=True)

    command = [
        "N_m3u8DL-RE.exe",
        "--save-dir", f"Downloads/{foldername}",
        "--tmp-dir", "Temp/",
        "--save-name", filename,
        "./temp.m3u8",
        "-M", "mp4"
    ]
    logger.info(f"Downloading {filename}...")
    subprocess.run(command)
    os.remove("./temp.m3u8")

# ===================================================================================================================================================== #

def download_subtitles(html, foldername, filename):
    """Download subtitles from HTML."""
    subtitles = extract_data(html, ["props", "initialProps", "pageProps", "prePlayerData", "dash", "data", "program", "stl"])
    if not subtitles:
        logger.warning("No subtitles found.")
        return

    foldername, filename = slugify(foldername), slugify(filename)
    for subtitle in subtitles:
        lang = subtitle["_name"]
        sub_url = f"https://meta.video.iqiyi.com{subtitle['srt']}"
        sub_path = f"./Downloads/{foldername}/{filename}.{lang}.srt"

        scraper = create_scraper()
        with open(sub_path, "w", encoding="utf-8") as file:
            file.write(scraper.get(sub_url).text)
        logger.info(f"Downloaded subtitle: {sub_path}")