import streamlit as st
from streamlit.components.v1 import html
import requests

# API 키 설정
KAKAO_API_KEY = "ddae3c29210c477e6e296cbcb8b717a4"  # JavaScript 키
KAKAO_REST_API_KEY = "9f024f555b6a52a8c7437d577f7deb0f"  # REST API 키
NAVER_CLIENT_ID = "SJEuYQimlmeqOEFBVP8_"
NAVER_CLIENT_SECRET = "jdr3EuEGKg"
GOOGLE_API_KEY = "AIzaSyDF2PjlBkUupABpDhmte4xXfdWH0kLTaUk"

def fetch_coordinates(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
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

def fetch_google_place_details(lat, lon):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": 2000,  # 2km 반경
        "type": "restaurant",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        st.error(f"Google Places API 요청 실패: {response.status_code}, 응답: {response.text}")
        return []

def kakao_map_html(lat, lon, places):
    places_script = ""
    for place in places:
        places_script += f"""
        var marker = new kakao.maps.Marker({{
            map: map,
            position: new kakao.maps.LatLng({place['geometry']['location']['lat']}, {place['geometry']['location']['lng']})
        }});
        var infowindow = new kakao.maps.InfoWindow({{
            content: '<div style="padding:5px;">{place['name']}</div>'
        }});
        kakao.maps.event.addListener(marker, 'mouseover', function() {{
            infowindow.open(map, marker);
        }});
        kakao.maps.event.addListener(marker, 'mouseout', function() {{
            infowindow.close();
        }});
        """

    return f"""
    <div id="map" style="width:100%;height:700px;position:relative;overflow:hidden;"></div>
    <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_API_KEY}"></script>
    <script>
        if (!window.kakaoMapInitialized) {{
            var container = document.getElementById('map');
            var options = {{
                center: new kakao.maps.LatLng({lat}, {lon}),
                level: 3
            }};
            var map = new kakao.maps.Map(container, options);
            window.kakaoMapInitialized = true;
            {places_script}
        }}
    </script>
    """

st.title("🍽️ 음식점 찾는 앱")
st.markdown("가까운 음식점을 찾아보세요. 지도를 통해 위치를 확인하고 음식점 정보를 확인할 수 있어요.")

address = st.text_input("📍 상세한 주소를 입력해주세요: XX동 XX구 or 도로명 주소")
restaurants = []

if st.button("🔍 그 근처 음식점 찾기"):
    lat, lon = fetch_coordinates(address)

    if lat is None or lon is None:
        st.error("유효한 주소를 입력해주세요.")
    else:
        restaurants = fetch_google_place_details(lat, lon)
        st.session_state["map_html"] = kakao_map_html(lat, lon, restaurants)

if "map_html" in st.session_state:
    html(st.session_state["map_html"], height=700, scrolling=True)

if restaurants:
    st.markdown("### 주변 음식점 목록:")
    for restaurant in restaurants:
        st.write(f"📌 {restaurant['name']} - {restaurant.get('vicinity', '주소 정보 없음')}")
else:
    st.write("음식점을 찾을 수 없습니다.")
