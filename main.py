import http.cookiejar
import re
import os
import json
import signal
import shutil
import time
import requests
from colorama import Fore, Style, init
from modules.cookies import load_cookies
from modules.iq import (
    fetch_html, 
    get_album_id, 
    get_episodes, 
    get_series_title, 
    get_title, 
    download_media,
    download_subtitles,
    get_video_m3u8
)
from modules.banners import banners, clear_screen
from modules.logging import setup_logging

# Initialize Colorama
init(autoreset=True)
logger = setup_logging("MAIN")

def display_menu(title, options):
    """Display a formatted menu and return the user's choice."""
    print(f"\n{Fore.CYAN}{'=' * 40}")
    print(f"{Fore.YELLOW}{title.center(40)}")
    print(f"{Fore.CYAN}{'=' * 40}")
    
    for idx, option in enumerate(options, start=1):
        print(f"{Fore.GREEN}[{idx}] {Fore.WHITE}{option}")
    print(f"{Fore.CYAN}{'=' * 40}")

    try:
        choice = int(input(f"{Fore.MAGENTA}\nEnter your choice: {Style.RESET_ALL}"))
        if choice < 1 or choice > len(options):
            raise ValueError
    except ValueError:
        print(f"{Fore.RED}\n⚠️ Invalid input. Please try again.{Style.RESET_ALL}")
        return display_menu(title, options)
    
    return choice

def choose_lang():
    """Prompt the user to select a language."""
    logger.debug("Prompting user for language selection.")
    options = [
        "English", "Simplified Chinese", "Traditional Chinese", "Bahasa Indonesia", 
        "Bahasa Malaysia", "Thai", "Vietnamese", "Japanese", "Português", "Español"
    ]
    choice = display_menu("Language Selection", options)
    languages = ['en_us', 'zh_cn', 'zh_tw', 'id_id', 'ms_my', 'th_th', 'vi_vn', 'ja', 'pt_br', 'es_mx']
    selected_lang = languages[choice - 1]
    print(f"\n{Fore.GREEN}✅ Selected language: {Fore.WHITE}{options[choice - 1]}{Style.RESET_ALL}")
    return selected_lang

def choose_res():
    """Prompt the user to select a resolution."""
    logger.debug("Prompting user for resolution selection.")
    options = ["1080p", "720p", "480p", "360p"]
    choice = display_menu("Resolution Selection", options)
    resolutions = [600, 400, 300, 200]
    selected_res = resolutions[choice - 1]
    print(f"\n{Fore.GREEN}✅ Selected resolution: {Fore.WHITE}{options[choice - 1]}{Style.RESET_ALL}")
    return selected_res

def main():
    """Main function to run the media downloader."""
    print(f"\n{Fore.MAGENTA}✨ Welcome to the Media Downloader ✨{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}Follow the prompts to configure your download preferences.{Style.RESET_ALL}\n")

    # Step 1: Language selection
    lang = choose_lang()
    logger.info(f"Selected language: {lang}")
    clear_screen()
    banners()

    res = choose_res()
    logger.info(f"Selected resolution: {res}p")
    clear_screen()
    banners()

    print(f"\n{Fore.CYAN}💡 Example URL: {Fore.WHITE}https://example.com/media{Style.RESET_ALL}")
    url = input(f"{Fore.MAGENTA}🔗 Enter the media URL: {Style.RESET_ALL}").strip().replace("album", "play")
    logger.info(f"Input URL: {url}")
    clear_screen()
    banners()

    print(f"\n{Fore.YELLOW}🔄 Loading cookies and fetching content...{Style.RESET_ALL}")
    
    try:
        cookies = load_cookies("cookies/cookies.txt")
        base_html = fetch_html(url, res, lang, cookies)
        episodes = get_episodes(base_html, lang)
        if episodes:
            series_title = get_series_title(base_html)  # Fixed the function call to get series title
            print(f"{Fore.YELLOW}Series Title: {Fore.WHITE}{series_title}{Style.RESET_ALL}")
            if input(f"\n{Fore.MAGENTA}Do you want to download the entire series? (y/n): {Style.RESET_ALL}").strip().lower() == "y":
                for episode_url in episodes:
                    episode_html = fetch_html(episode_url, res, lang, cookies)
                    title = get_title(episode_html)
                    get_video_m3u8(episode_html)
                    download_media(series_title, title)
                    download_subtitles(episode_html, series_title, title)
                    print(f"\n{Fore.CYAN}📂 Downloading media... {Fore.WHITE}{title}{Style.RESET_ALL}")
            else:
                logger.info("Skipping series download.")
        else:
            title = get_title(base_html)
            get_video_m3u8(base_html)
            download_media(title, title)
            download_subtitles(base_html, title, title)
            print(f"\n{Fore.GREEN}✅ Download complete! Check your output folder.{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"An error occurred during download: {e}")
        print(f"\n{Fore.RED}❌ An error occurred during the download process. Please try again.{Style.RESET_ALL}")

if __name__ == "__main__":
    clear_screen()
    banners()
    main()