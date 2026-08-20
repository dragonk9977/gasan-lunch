# ==========================================================
# 11. Selenium 종료 및 구글 지도 생성 (여백 터치 팝업 유지, 팝업 터치 시 닫힘 및 원위치 복귀)
# ==========================================================

driver.quit()

print()
print("=" * 60)
print("자동 수집 완료!")
print("=" * 60)

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

/* 팝업 닫기(X) 버튼 확대 */
.leaflet-popup-close-button {
    width: 40px !important;
    height: 40px !important;
    padding: 8px !important;
    font-size: 26px !important;
    color: #e74c3c !important;
    font-weight: bold !important;
}

/* 우측 상단 '전체보기' 버튼 스타일 */
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
                window.mapObj = mapObj; // 팝업 내부에서 참조할 수 있도록 전역 등록
                initialCenter = mapObj.getCenter();
                initialZoom = mapObj.getZoom();

                // 우측 상단 전체보기 버튼
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

                // 팝업이 닫힐 때 원위치 복귀
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
    # ★ 팝업 창 안쪽을 터치하면 팝업이 닫히며 초기 지도 위치로 이동하도록 설정
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
        <div style="font-size:11px; color:#888; margin-top:8px; font-style:italic;">(이미지나 상자를 터치하면 닫힙니다)</div>
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
        # ★ close_onclick=False를 주어 지도 여백을 터치해도 팝업이 닫히지 않도록 고정
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

print()
print("=" * 60)
print("🎉 여백 터치 유지 및 팝업 터치 시 닫힘/원위치 복귀 적용 완료!")
print(f"📄 파일 : {output_file}")
print("=" * 60)
