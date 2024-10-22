import streamlit as st
from streamlit.components.v1 import html
import requests

KAKAO_API_KEY = "d693cf4169b24f12ec19b0a6713f58f4"
KAKAO_REST_API_KEY = "8741ff3930e0c669e15cf0781c95c8a6"

### 주소를 입력받아 위도와 경도를 가져오는 함수 ###
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
        st.error(f"카카오코딩 API 요청 실패: {response.status_code}, 응답: {response.text}")
    return None, None

### 위도, 경도를 기반으로 음식점 검색 ###
def fetch_restaurants(lat, lon):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": "음식점",
        "x": lon,
        "y": lat,
        "radius": 2000  ### 반경 2km 내 검색 ###
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('documents', [])
    else:
        st.error(f"음식점 정보 API 요청 실패: {response.status_code}, 응답: {response.text}")
        return []

### 지도를 HTML로 생성 ###
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
    <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_API_KEY}"></script>
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

### Streamlit 시작 ###
st.title("🍽️ 음식점 찾는 앱")
st.markdown("<p style='font-size: 16px;'>가까운 음식점을 찾아보세요. 지도를 통해 위치를 확인하고 음식점 정보를 확인하세요!</p>", unsafe_allow_html=True)

address = st.text_input("📍 상세한 주소를 입력해주세요:")

if st.button("🔍 그 근처 음식점 찾기"):
    lat, lon = fetch_coordinates(address)

    ### lat, lon 값이 없을 경우 기본 좌표 설정 ###
    if lat is None or lon is None:
        st.error("유효한 주소를 입력해주세요.")
    else:
        restaurants = fetch_restaurants(lat, lon)

        if restaurants:
            ### Streamlit의 컬럼 레이아웃을 사용하여 지도를 왼쪽에, 음식점 목록을 오른쪽에 배치 ###
            col1, col2 = st.columns([2, 1])  # 지도를 더 크게 하기 위해 비율을 2:1로 조정

            with col1:
                ### 지도를 생성하여 표시 (정사각형 형태로 더 크게) ###
                map_html = kakao_map_html(lat, lon, restaurants)
                html(map_html, height=700)  # 지도를 더 크게, 높이를 700으로 설정하여 정사각형에 가깝게 표시

            with col2:
                st.markdown("<h3 style='margin-top: 20px;'>주변 음식점 목록:</h3>", unsafe_allow_html=True)
                for restaurant in restaurants:
                    ### 음식점 정보 카드 스타일로 표시 (이미지 부분 제거) ###
                    st.markdown(f"""
                    <div class="card" style="margin-bottom: 20px; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);">
                        <div class="card-body">
                            <h4 class="card-title" style="font-weight: bold; color: #007BFF;">{restaurant['place_name']}</h4>
                            <p class="card-text"><strong>주소:</strong> {restaurant['road_address_name']}</p>
                            <p class="card-text"><strong>전화번호:</strong> {restaurant['phone']}</p>
                            <a href="{restaurant['place_url']}" target="_blank" style="text-decoration: none; background-color: #007BFF; color: white; padding: 10px 15px; border-radius: 5px;">새 창에서 더보기</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.write("음식점을 찾을 수 없습니다.")

### 스타일 개선 ###
st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            height: 50px;
            font-size: 18px;
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }0
        .stButton>button:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True)
