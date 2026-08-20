import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import folium

# MacroDroid로부터 전달받은 메뉴 텍스트
payload_text = os.environ.get("MENU_TEXT", "")

scraped_data = []

# Selenium 옵션 설정 (헤드리스 모드)
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,800")
# 봇 탐지 방지를 위한 User-Agent 설정
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

try:
    # 1. 런치타임 (스레드 데이터 처리)
    if payload_text:
        # MacroDroid로 받은 텍스트를 카드 형태로 깔끔하게 스타일링
        lunchtime_html = f"""
        <div style='font-size:15px; line-height:1.6; color:#333; text-align:left; padding:12px; background-color:#f9f9f9; border-radius:10px; border-left: 5px solid #2ecc71;'>
            <strong style="color:#27ae60;">📢 오늘의 메뉴 (런치타임)</strong><br>
            <hr style="border:0; border-top:1px solid #ddd; margin:10px 0;">
            {payload_text.replace(chr(10), '<br>')}
        </div>
        """
    else:
        try:
            driver.get("https://www.threads.net/@lunchtime_ypp")
            time.sleep(5)
            posts = driver.find_elements(By.CSS_SELECTOR, 'div[data-pressable-container="true"]')
            if posts:
                lunchtime_html = posts[0].get_attribute('innerHTML')
            else:
                lunchtime_html = "<p>게시물을 불러오지 못했습니다.</p>"
        except Exception as e:
            lunchtime_html = f"<p>스레드 크롤링 실패: {e}</p>"

    scraped_data.append({
        'name': '런치타임',
        'lat': 37.4785,
        'lng': 126.8810,
        'walk_min': 3,
        'dist': 200,
        'html': lunchtime_html
    })

    # 2. 온정찬 (카카오 채널 크롤링 - 안정적인 대기 로직 적용)
    try:
        driver.get("https://pf.kakao.com/_UIdXn/posts")
        
        # 요소가 나올 때까지 최대 10초 대기 (검증된 방식)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.item_post")))
        
        kakao_posts = driver.find_elements(By.CSS_SELECTOR, 'div.item_post')
        
        if kakao_posts:
            # 게시물 내용을 스타일링하여 삽입
            content = kakao_posts[0].get_attribute('innerHTML')
            onjeongchan_html = f"<div style='font-size:14px; line-height:1.5; text-align:left;'>{content}</div>"
        else:
            onjeongchan_html = "<p>온정찬 게시물 영역을 찾지 못했습니다.</p>"
            
    except Exception as e:
        onjeongchan_html = f"<p>카카오 크롤링 실패: {e}</p>"

    scraped_data.append({
        'name': '온정찬',
        'lat': 37.4795,  # 가산디지털1로 75-15 부근
        'lng': 126.8825,
        'walk_min': 4,
        'dist': 250,
        'html': onjeongchan_html
    })

except Exception as e:
    print(f"전체 프로세스 에러 발생: {e}")
finally:
    driver.quit()

# 3. 구글 지도 생성 (folium)
menu_map = folium.Map(
    location=[37.4790, 126.8820],
    zoom_start=17,
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google'
)

# [CSS 및 버튼 스크립트]
custom_header = """
<style>
.reset-map-btn { position: fixed; top: 15px; right: 15px; z-index: 99999; background: #fff; border: 3px solid #000; padding: 10px 16px; font-weight: bold; border-radius: 10px; cursor: pointer; }
</style>
<script>
window.addEventListener('load', function() {
    setTimeout(function() {
        for (var key in window) {
            if (window[key] && window[key] instanceof L.Map) {
                var mapObj = window[key];
                var btn = document.createElement('div');
                btn.innerHTML = '🗺️ 전체보기';
                btn.className = 'reset-map-btn';
                btn.onclick = function() { mapObj.closePopup(); mapObj.setView([37.4790, 126.8820], 17); };
                document.body.appendChild(btn);
                break;
            }
        }
    }, 500);
});
</script>
"""
menu_map.get_root().html.add_child(folium.Element(custom_header))

# 마커 추가
for data in scraped_data:
    popup_html = f"""
    <div style="width:300px; text-align:center;">
        <h3 style="margin:10px 0; font-size:18px;">{data['name']}</h3>
        <p style="margin:0 0 10px 0; font-size:12px; color:#e74c3c;">🏢 도보 {data['walk_min']}분 ({data['dist']}m)</p>
        <hr>{data['html']}
    </div>
    """
    
    # 텍스트 마커
    folium.Marker(
        location=[data["lat"], data["lng"]],
        popup=folium.Popup(popup_html, max_width=350),
        tooltip=data["name"],
        icon=folium.DivIcon(html=f'<div style="background:#fff; border:2px solid #000; padding:5px; border-radius:5px; font-weight:bold;">{data["name"]}</div>')
    ).add_to(menu_map)

# 지도 저장
menu_map.save("gasan_lunch_map.html")
print("지도 생성 완료!")
