import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import folium

# MacroDroid로부터 전달받은 메뉴 텍스트 (없으면 테스트 문구)
payload_text = os.environ.get("MENU_TEXT", "")
if not payload_text:
    payload_text = "[테스트 모드] 런치타임 알림 대기 중..."

scraped_data = []

# Selenium 옵션 설정 (봇 탐지 회피 강화)
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,800")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)

try:
    # ----------------------------------------------------
    # 1. 런치타임 (스레드 / MacroDroid 연동)
    # ----------------------------------------------------
    try:
        lunchtime_html = f"""
        <div style='font-size:15px; line-height:1.6; color:#333; text-align:left; padding:12px; background-color:#f9f9f9; border-radius:10px; border-left: 5px solid #2ecc71;'>
            <strong style="color:#27ae60;">📢 오늘의 메뉴 (런치타임)</strong><br>
            <hr style="border:0; border-top:1px solid #ddd; margin:10px 0;">
            {payload_text.replace(chr(10), '<br>')}
        </div>
        """
    except Exception as e:
        lunchtime_html = f"<p>런치타임 데이터 처리 에러: {e}</p>"

    scraped_data.append({
        'name': '런치타임',
        'lat': 37.4785,
        'lng': 126.8810,
        'walk_min': 3,
        'dist': 200,
        'html': lunchtime_html
    })

    # ----------------------------------------------------
    # 2. 온정찬 (카카오 채널 크롤링)
    # ----------------------------------------------------
    onjeongchan_html = "<p>온정찬 정보를 불러오는 중입니다...</p>"
    try:
        driver.get("https://pf.kakao.com/_UIdXn/posts")
        time.sleep(5) # 페이지 로딩 대기
        
        # 카카오 채널 게시물 영역 탐색 (다중 셀렉터 적용)
        posts = driver.find_elements(By.CSS_SELECTOR, 'div.item_post, div.wrap_post, div.txt_post')
        
        if posts:
            content = posts[0].get_attribute('innerHTML')
            onjeongchan_html = f"""
            <div style='font-size:14px; line-height:1.5; text-align:left; max-height:300px; overflow-y:auto;'>
                <strong style="color:#e67e22;">🔥 온정찬 오늘의 메뉴</strong><br>
                <hr style="border:0; border-top:1px solid #ddd; margin:8px 0;">
                {content}
            </div>
            """
        else:
            onjeongchan_html = "<p style='color:#e74c3c;'>온정찬 게시물을 찾지 못했습니다. (링크 또는 구조 확인 필요)</p>"
            
    except Exception as e:
        onjeongchan_html = f"<p style='color:#e74c3c;'>카카오 크롤링 에러: {e}</p>"

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

# ----------------------------------------------------
# 3. 구글 지도 생성 (Folium)
# ----------------------------------------------------
menu_map = folium.Map(
    location=[37.4790, 126.8820],
    zoom_start=16,
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google'
)

# 상단 전체보기 버튼 및 팝업 닫기 스크립트
custom_header = """
<style>
.reset-map-btn { position: fixed; top: 15px; right: 15px; z-index: 99999; background: #fff; border: 3px solid #000; padding: 10px 16px; font-weight: bold; border-radius: 10px; cursor: pointer; box-shadow: 0px 4px 10px rgba(0,0,0,0.3); }
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
                btn.onclick = function() { mapObj.closePopup(); };
                document.body.appendChild(btn);
                break;
            }
        }
    }, 500);
});
</script>
"""
menu_map.get_root().html.add_child(folium.Element(custom_header))

# 마커 일괄 생성
for data in scraped_data:
    popup_html = f"""
    <div style="width:310px; text-align:center; padding:5px;">
        <h3 style="margin:8px 0; font-size:18px; color:#333;">{data['name']}</h3>
        <p style="margin:0 0 10px 0; font-size:12px; color:#e74c3c; font-weight:bold;">🏢 회사에서 도보 {data['walk_min']}분 ({data['dist']}m)</p>
        <hr style="margin:5px 0;">
        {data['html']}
    </div>
    """
    
    folium.Marker(
        location=[data["lat"], data["lng"]],
        popup=folium.Popup(popup_html, max_width=350),
        tooltip=data["name"],
        icon=folium.DivIcon(html=f'<div style="background:#fff; border:2px solid #000; padding:5px 10px; border-radius:6px; font-weight:bold; box-shadow:0 2px 5px rgba(0,0,0,0.3); font-size:14px;">{data["name"]}</div>')
    ).add_to(menu_map)

# 두 마커가 모두 화면에 잘 들어오도록 지도 영역 자동 조절
all_lats = [d["lat"] for d in scraped_data]
all_lngs = [d["lng"] for d in scraped_data]
if all_lats and all_lngs:
    menu_map.fit_bounds([[min(all_lats), min(all_lngs)], [max(all_lats), max(all_lngs)]], padding=(50, 50))

# 지도 파일 저장
output_file = "gasan_lunch_map.html"
menu_map.save(output_file)
print("지도가 성공적으로 생성되었습니다!")
