import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import folium

# MacroDroid로부터 전달받은 메뉴 텍스트 (환경변수에서 읽어옴)
payload_text = os.environ.get("MENU_TEXT", "")

scraped_data = []

# Selenium 옵션 설정
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,800")

driver = webdriver.Chrome(options=options)

try:
    # 1. 런치타임 (스레드 크롤링 또는 MacroDroid 페이로드 사용)
    if payload_text:
        lunchtime_html = f"<div style='font-size:14px; line-height:1.5; text-align:left;'>{payload_text.replace(chr(10), '<br>')}</div>"
    else:
        try:
            driver.get("https://www.threads.net/@lunchtime_ypp")
            time.sleep(4)
            posts = driver.find_elements(By.CSS_SELECTOR, 'div[data-pressable-container="true"]')
            if posts:
                lunchtime_html = posts[0].get_attribute('innerHTML')
            else:
                lunchtime_html = "<p>스레드 게시물을 불러오지 못했습니다.</p>"
        except Exception as e:
            lunchtime_html = f"<p>크롤링 실패: {e}</p>"

    scraped_data.append({
        'name': '런치타임',
        'lat': 37.4785,
        'lng': 126.8810,
        'walk_min': 3,
        'dist': 200,
        'html': lunchtime_html
    })

    # 2. 온정찬 (카카오 채널 크롤링)
    # 주소: 서울 금천구 가산디지털1로 75-15
    try:
        driver.get("https://pf.kakao.com/_UIdXn/posts")
        time.sleep(4)
        kakao_posts = driver.find_elements(By.CSS_SELECTOR, 'div.wrap_post, div.item_post')
        if kakao_posts:
            onjeongchan_html = kakao_posts[0].get_attribute('innerHTML')
        else:
            onjeongchan_html = "<p>온정찬 오늘의 메뉴가 아직 올라오지 않았습니다.</p>"
    except Exception as e:
        onjeongchan_html = f"<p>온정찬 크롤링 실패: {e}</p>"

    scraped_data.append({
        'name': '온정찬',
        'lat': 37.4795,  # 가산디지털1로 75-15 부근 좌표 (필요시 미세조정 가능)
        'lng': 126.8825,
        'walk_min': 4,
        'dist': 250,
        'html': onjeongchan_html
    })

except Exception as e:
    print(f"전체 프로세스 에러 발생: {e}")
finally:
    driver.quit()

# 3. 구글 지도 생성 (모바일 최적화 및 인터랙션 적용)
menu_map = folium.Map(
    location=[37.4795, 126.8820],
    zoom_start=16,
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google'
)

custom_header = """
<style>
@font-face {
    font-family: 'KakaoBigFont';
    src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2503@1.0/KakaoBigSans-Regular.woff2') format('woff2');
    font-weight: 400;
}
* {
    font-family: 'KakaoBigFont', sans-serif !important;
}
.leaflet-popup-close-button {
    width: 40px !important;
    height: 40px !important;
    padding: 8px !important;
    font-size: 26px !important;
    color: #e74c3c !important;
    font-weight: bold !important;
}
.reset-map-btn {
    position: fixed;
    top: 15px;
    right: 15px;
    z-index: 99999;
    background: #ffffff;
    border: 3px solid #000000;
    padding: 10px 16px;
    font-weight: bold;
    font-size: 15px;
    border-radius: 10px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    cursor: pointer;
    color: #111;
}
</style>
<script>
let initialCenter = null;
let initialZoom = null;
let mapObj = null;

window.addEventListener('load', function() {
    setTimeout(function() {
        for (var key in window) {
            if (window[key] && window[key] instanceof L.Map) {
                mapObj = window[key];
                window.mapObj = mapObj;
                initialCenter = mapObj.getCenter();
                initialZoom = mapObj.getZoom();

                var btn = document.createElement('div');
                btn.innerHTML = '🗺️ 전체보기';
                btn.className = 'reset-map-btn';
                btn.onclick = function() {
                    if (mapObj) {
                        mapObj.closePopup();
                        if (initialCenter && initialZoom) {
                            mapObj.setView(initialCenter, initialZoom);
                        }
                    }
                };
                document.body.appendChild(btn);

                mapObj.on('popupclose', function() {
                    if (initialCenter && initialZoom) {
                        mapObj.setView(initialCenter, initialZoom);
                    }
                });
                break;
            }
        }
    }, 400);
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (mapObj) {
            mapObj.closePopup();
        }
    }
});
</script>
"""
menu_map.get_root().html.add_child(folium.Element(custom_header))

for data in scraped_data:
    popup_html = f"""
    <div style="width:320px; text-align:center; padding-top:10px; cursor:pointer;" onclick="if(window.mapObj) {{ window.mapObj.closePopup(); }}">
        <h3 style="margin:5px 0; font-size:20px; color:#333;">{data['name']}</h3>
        <p style="margin:0 0 10px 0; font-size:13px; color:#e74c3c; font-weight:bold;">
            🏢 회사에서 도보 약 {data['walk_min']}분 ({data['dist']}m)
        </p>
        <hr style="margin:5px 0 10px 0;">
        <div style="width:100%; overflow:visible; text-align:center;">
            {data['html']}
        </div>
        <div style="font-size:11px; color:#888; margin-top:8px; font-style:italic;">(상자를 터치하면 닫힙니다)</div>
    </div>
    """

    custom_icon = folium.DivIcon(
        icon_size=(150, 50),
        icon_anchor=(75, 25),
        html=f"""
        <div style="
            background-color: rgba(255, 255, 255, 0.95);
            border: 3px solid #000000;
            padding: 6px 12px;
            font-weight: bold;
            font-size: 15px;
            color: #111111;
            border-radius: 8px;
            white-space: nowrap;
            box-shadow: 0px 4px 8px rgba(0,0,0,0.3);
            text-align: center;
        ">
            {data['name']}
        </div>
        """
    )

    folium.Marker(
        location=[data["lat"], data["lng"]],
        popup=folium.Popup(popup_html, max_width=380, close_onclick=False),
        tooltip=data["name"],
        icon=custom_icon
    ).add_to(menu_map)

all_lats = [data["lat"] for data in scraped_data]
all_lngs = [data["lng"] for data in scraped_data]

if all_lats and all_lngs:
    menu_map.fit_bounds(
        [
            [min(all_lats), min(all_lngs)],
            [max(all_lats), max(all_lngs)]
        ],
        padding=(30, 30)
    )

output_file = "gasan_lunch_map.html"
menu_map.save(output_file)
print("지도가 성공적으로 생성되었습니다!")
