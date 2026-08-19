import os
import time
import json
import base64
from io import BytesIO
from datetime import datetime

import folium
from PIL import Image
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================================
# [수정] 1. 사용자 설정 및 깃허브 이벤트 데이터 가져오기
# ==========================================================

def get_manual_menu_from_github_event():
    """깃허브 이벤트(MacroDroid 전송)로부터 데이터를 가져오는 함수"""
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if event_path and os.path.exists(event_path):
        try:
            with open(event_path, 'r') as f:
                event_data = json.load(f)
                return event_data.get('client_payload', {}).get('menu_text', None)
        except:
            pass
    return None

OJEONG_IMAGE_PATH = "오정메뉴.jpg"
OFFICE_ADDRESS = "서울 금천구 가산디지털2로 30"

# ==========================================================
# 2. 오늘 날짜 / 요일
# ==========================================================
today = datetime.now()
weekdays = ["월", "화", "수", "목", "금", "토", "일"]
today_weekday_index = today.weekday()
today_weekday = weekdays[today_weekday_index]
today_date_str_space = f"{today.month}월 {today.day}일"
today_date_str_nospace = f"{today.month}월{today.day}일"
ojeong_weekday_index = min(today_weekday_index, 4)

print(f"\n{'='*60}\n오늘 날짜 : {today_date_str_space} ({today_weekday}요일)\n{'='*60}")

# (중간 생략: 3~9번 함수는 기존과 동일하게 유지하시면 됩니다.)
# ... crop_ojeong_by_weekday, get_kakao_profile_image, get_kakao_first_image, get_instagram_menu 함수들을 그대로 두세요 ...

# 아래는 10번 식당별 메뉴 수집 부분만 바꾸시면 됩니다.

# ==========================================================
# 10. 식당별 메뉴 수집 (★이 부분만 교체하세요)
# ==========================================================

scraped_data = []
# [추가] 깃허브 이벤트로 들어온 메뉴 확인
manual_menu = get_manual_menu_from_github_event() 

print(f"\n{'='*60}\n자동 수집 시작")
if manual_menu:
    print("  -> MacroDroid로부터 데이터를 받았습니다! (인스타 크롤링 건너뜀)")
print(f"{'='*60}")

for item in cafeteria_list:
    print(f"\n[{item['name']}] 정보 수집 중...")
    lat, lng = get_coords(item["address"])
    dist, walk_min = calculate_walking_info((lat, lng))
    html_content = ""

    if item["type"] == "ojeong":
        src = crop_ojeong_by_weekday(item["url"])
        html_content = f'<img src="{src}" style="display:block; margin:0 auto; max-width:100%; width:auto; height:auto;">' if src else "<div>오정 메뉴를 불러오지 못했습니다.</div>"

    elif item["type"] == "kakao_profile":
        img_src = get_kakao_profile_image(driver, item["url"], item["name"])
        html_content = f'<img src="{img_src}" style="display:block; margin:0 auto; max-width:100%; max-height:700px; width:auto; height:auto; border-radius:6px;">' if img_src else '<div style="padding:20px; font-weight:bold;">카카오 메뉴 이미지를 찾지 못했습니다.</div>'

    elif item["type"] == "kakao_first":
        img_src = get_kakao_first_image(driver, item["url"], item["name"])
        html_content = f'<img src="{img_src}" style="display:block; margin:0 auto; max-width:100%; max-height:700px; width:auto; height:auto; border-radius:6px;">' if img_src else '<div style="padding:20px; font-weight:bold;">카카오 메뉴 이미지를 찾지 못했습니다.</div>'

    elif item["type"] == "instagram":
        # ★ [수정] 런치타임은 수동 데이터가 있으면 그걸 쓰고, 없으면 기존대로 크롤링
        if manual_menu:
            html_content = f'''<div style="background-color:#f9f9f9; border:1px solid #ddd; padding:15px; border-radius:8px; text-align:left; font-size:15px; line-height:1.7; color:#333;">{manual_menu.replace(chr(10), '<br>')}</div>'''
        else:
            html_content = get_instagram_menu(driver, item["url"])

    scraped_data.append({"name": item["name"], "lat": lat, "lng": lng, "dist": dist, "walk_min": walk_min, "html": html_content})
    time.sleep(1.5)

# (11번 이후 코드는 기존과 동일하게 유지하세요!)
