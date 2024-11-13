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

### 위도, 경도를 기반으로 음식점 검색 (페이지네이션 추가) ###
def fetch_restaurants(lat, lon, keyword="음식점"):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": f"{keyword}",
        "x": lon,
        "y": lat,
        "radius": 2000,  ### 반경 2km 내 검색 ###
        "size": 15,  ### 한 페이지에 최대 15개의 결과 ###
        "page": 1   ### 첫 페이지부터 시작 ###
    }

    all_restaurants = []
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            documents = data.get('documents', [])
            all_restaurants.extend(documents)

            # 현재 페이지가 마지막 페이지인지 확인
            if not data.get('meta', {}).get('is_end', True):
                params['page'] += 1  # 다음 페이지로 이동
            else:
                break
        else:
            st.error(f"음식점 정보 API 요청 실패: {response.status_code}, 응답: {response.text}")
            break

    return all_restaurants

### 지도를 HTML로 생성 ###
def kakao_map_html(lat, lon, places):
    markers_script = ""

    # 현재 위치 마커 추가
    markers_script += f"""
    var currentPosition = new kakao.maps.LatLng({lat}, {lon});
    var currentMarker = new kakao.maps.Marker({{
        position: currentPosition,
        map: map,
        title: "현재 위치",
        zIndex: 2,
        image: new kakao.maps.MarkerImage("https://cdn-icons-png.flaticon.com/512/684/684908.png", new kakao.maps.Size(40, 40))
    }});

    // 반경 2km의 원을 지도에 그리기
    var circle = new kakao.maps.Circle({{
        center: currentPosition,  // 원의 중심 좌표
        radius: 2000,  // 반경 (단위: 미터)
        strokeWeight: 3,  // 선의 두께
        strokeColor: '#FF0000',  // 선의 색깔
        strokeOpacity: 0.8,  // 선의 불투명도 (0 ~ 1)
        fillColor: '#FF0000',  // 채우기 색깔
        fillOpacity: 0.2  // 채우기 불투명도 (0 ~ 1)
    }});
    circle.setMap(map);
    """

    # 각 음식점에 대한 마커 추가
    for idx, place in enumerate(places):
        distance = place.get('distance', '정보 없음')  # 거리 정보가 없으면 '정보 없음'으로 표시
        place_url = place.get('place_url', '#')  # 상세 페이지 URL 가져오기

        markers_script += f"""
        (function() {{
            var position = new kakao.maps.LatLng({place['y']}, {place['x']});
            
            // 마커 이미지 커스터마이징 (더 작게 변경된 마커 이미지)
            var imageSrc = "https://cdn-icons-png.flaticon.com/512/484/484167.png";  // 사용할 마커 이미지 URL (예: Flaticon에서 가져온 URL)
            var imageSize = new kakao.maps.Size(30, 30);        // 마커 이미지의 크기 (작게 설정)
            var imageOption = {{ offset: new kakao.maps.Point(15, 30) }}; // 마커 이미지의 중심 좌표
            
            // 마커 이미지 생성
            var markerImage = new kakao.maps.MarkerImage(imageSrc, imageSize, imageOption);
            
            var marker = new kakao.maps.Marker({{
                position: position,
                map: map,
                image: markerImage  // 커스텀 마커 이미지 적용
            }});

            var infowindow = new kakao.maps.InfoWindow({{
                content: '<div style="padding:5px;">{place['place_name']}<br>거리: {distance}m</div>'
            }});

            // 마커에 마우스를 올렸을 때 인포윈도우 표시
            kakao.maps.event.addListener(marker, 'mouseover', function() {{
                infowindow.open(map, marker);
            }});

            // 마커에서 마우스를 내렸을 때 인포윈도우 닫기
            kakao.maps.event.addListener(marker, 'mouseout', function() {{
                infowindow.close();
            }});

            // 마커를 클릭하면 해당 매장 정보 페이지로 이동
            kakao.maps.event.addListener(marker, 'click', function() {{
                window.open("{place_url}", "_blank");
            }});
        }})();
        """

    # HTML에 삽입되는 JavaScript 코드를 구성합니다.
    return f"""
    <div id="map" style="width:100%;height:600px; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);"></div>
    <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_API_KEY}&libraries=services"></script>
    <script>
        var container = document.getElementById('map');
        var options = {{
            center: new kakao.maps.LatLng({lat}, {lon}),
            level: 3
        }};
        var map = new kakao.maps.Map(container, options);
        {markers_script}
    </script>
    """

### Streamlit 시작 ###
st.set_page_config(layout="wide")  # 페이지 레이아웃을 가로로 넓게 설정

st.title("🍽️ 음식점 찾는 앱")
st.markdown("<p style='font-size: 16px;'>가까운 음식점을 찾아보세요. 지도를 통해 위치를 확인하고 음식점 정보를 확인하세요!</p>", unsafe_allow_html=True)

address = st.text_input("📍 상세한 주소를 입력해주세요:")

# 맛집 필터 옵션 추가
filter_option = st.checkbox("맛집만 보기")

if st.button("🔍 그 근처 음식점 찾기"):
    keyword = "맛집" if filter_option else "음식점"
    lat, lon = fetch_coordinates(address)

    ### lat, lon 값이 없을 경우 기본 좌표 설정 ###
    if lat is None or lon is None:
        st.error("유효한 주소를 입력해주세요.")
    else:
        restaurants = fetch_restaurants(lat, lon, keyword=keyword)

        if restaurants:
            ### 지도와 음식점 목록을 세로로 배치 ###
            st.markdown("<h3 style='margin-top: 20px;'>주변 음식점 위치:</h3>", unsafe_allow_html=True)
            map_html = kakao_map_html(lat, lon, restaurants)
            html(map_html, height=600)  # 지도를 상단에 크게 표시

            st.markdown("<h3 style='margin-top: 20px;'>주변 음식점 목록:</h3>", unsafe_allow_html=True)
            # 음식점 목록을 화면의 전체 너비를 사용해 세 개의 열로 표시
            cols = st.columns(3)
            for idx, restaurant in enumerate(restaurants):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="card" style="margin-bottom: 20px; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);">
                        <img src="https://cdn-icons-png.flaticon.com/512/2921/2921822.png" alt="음식점 이미지" style="width:100%;height:150px;object-fit:cover;border-top-left-radius: 10px;border-top-right-radius: 10px;">
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
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True) 
