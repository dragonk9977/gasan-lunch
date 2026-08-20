import os
import folium

# MacroDroid로부터 전달받은 메뉴 텍스트
payload_text = os.environ.get("MENU_TEXT", "")
if not payload_text:
    payload_text = "메뉴 정보 대기 중..."

scraped_data = []

# 1. 밥심
scraped_data.append({
    'name': '밥심',
    'lat': 37.4812,
    'lng': 126.8815,
    'walk_min': 4,
    'dist': 250,
    'html': "<div style='font-size:14px; text-align:center;'>밥심 정보</div>"
})

# 2. 런치투게더
scraped_data.append({
    'name': '런치투게더',
    'lat': 37.4780,
    'lng': 126.8850,
    'walk_min': 5,
    'dist': 320,
    'html': "<div style='font-size:14px; text-align:center;'>런치투게더 정보</div>"
})

# 3. 런치타임 (MacroDroid 연동 데이터)
lunchtime_html = f"""
<div style='font-size:15px; line-height:1.6; color:#333; text-align:left; padding:12px; background-color:#f9f9f9; border-radius:10px; border-left: 5px solid #2ecc71;'>
    <strong style="color:#27ae60;">📢 오늘의 메뉴 (런치타임)</strong><br>
    <hr style="border:0; border-top:1px solid #ddd; margin:10px 0;">
    {payload_text.replace(chr(10), '<br>')}
</div>
"""
scraped_data.append({
    'name': '런치타임',
    'lat': 37.4785,
    'lng': 126.8820,
    'walk_min': 3,
    'dist': 180,
    'html': lunchtime_html
})

# 구글 지도 생성
menu_map = folium.Map(
    location=[37.4790, 126.8820],
    zoom_start=16,
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google'
)

# 마커 추가
for data in scraped_data:
    popup_html = f"""
    <div style="width:250px; text-align:center; padding:5px;">
        <h3 style="margin:8px 0;">{data['name']}</h3>
        <p style="font-size:12px;">도보 {data['walk_min']}분 ({data['dist']}m)</p>
        <hr>{data['html']}
    </div>
    """
    folium.Marker(
        location=[data["lat"], data["lng"]],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=data["name"],
        icon=folium.DivIcon(html=f'<div style="background:#fff; border:2px solid #000; padding:5px 10px; font-weight:bold; border-radius:5px;">{data["name"]}</div>')
    ).add_to(menu_map)

# 지도 저장
menu_map.save("gasan_lunch_map.html")
print("지도 생성 완료!")
