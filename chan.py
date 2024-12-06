import streamlit as st
from streamlit.components.v1 import html
import requests

KAKAO_API_KEY = "ddae3c29210c477e6e296cbcb8b717a4"
KAKAO_REST_API_KEY = "9f024f555b6a52a8c7437d577f7deb0f"

NAVER_CLIENT_ID = "SJEuYQimlmeqOEFBVP8_"
NAVER_CLIENT_SECRET = "jdr3EuEGKg"


def fetch_coordinates(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}",
        "User-Agent": "os/web origin/myapp"
    }
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        documents = response.json().get('documents', [])
        if documents:
            return float(documents[0]['y']), float(documents[0]['x'])
        else:
            st.error("주소를 찾을 수 없습니다.")
    else:
        st.error(f"카카오 API 요청 실패: {response.status_code}, 응답: {response.text}")
    return None, None


def fetch_restaurants(lat, lon):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}",
        "User-Agent": "os/web origin/myapp"
    }
    params = {
        "query": "음식점",
        "x": lon,
        "y": lat,
        "radius": 2000  
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('documents', [])
    else:
        st.error(f"음식점 정보 API 요청 실패: {response.status_code}, 응답: {response.text}")
        return []


def kakao_map_html(lat, lon, places):
    places_script = ""
    for place in places:
        places_script += f"""
        var marker = new kakao.maps.Marker({{
            map: map,
            position: new kakao.maps.LatLng({place['y']}, {place['x']})
        }});
        var infowindow = new kakao.maps.InfoWindow({{
            content: '<div style="padding:5px;">{place['place_name']}</div>'
        }});
        kakao.maps.event.addListener(marker, 'mouseover', function() {{
            infowindow.open(map, marker);
        }});
        kakao.maps.event.addListener(marker, 'mouseout', function() {{
            infowindow.close();
        }});
        """

    return f"""
    <div id="map" style="width:100%;height:700px; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);"></div>
    <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_API_KEY}&libraries=services"></script>
    <script>
        var container = document.getElementById('map');
        var options = {{
            center: new kakao.maps.LatLng({lat}, {lon}),
            level: 3
        }};
        var map = new kakao.maps.Map(container, options);
        {places_script}
    </script>
    """


st.title("🍽️ 음식점 찾는 앱")
st.markdown("<p style='font-size: 16px;'>가까운 음식점을 찾아보세요. 지도를 통해 위치를 확인하고 음식점 정보를 확인할 수 있어요</p>", unsafe_allow_html=True)

address = st.text_input("📍 상세한 주소를 입력해주세요: XX동 XX구 or 도로명 주소")

restaurants = []

if st.button("🔍 그 근처 음식점 찾기"):
    lat, lon = fetch_coordinates(address)

    if lat is None or lon is None:
        st.error("유효한 주소를 입력해주세요.")
    else:
        restaurants = fetch_restaurants(lat, lon)

if restaurants:
    map_html = kakao_map_html(lat, lon, restaurants)
    html(map_html, height=700, scrolling=True)
