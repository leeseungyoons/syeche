import streamlit as st
from streamlit.components.v1 import html
import requests

KAKAO_API_KEY = "ddae3c29210c477e6e296cbcb8b717a4"
KAKAO_REST_API_KEY = "9f024f555b6a52a8c7437d577f7deb0f"

NAVER_CLIENT_ID = "SJEuYQimlmeqOEFBVP8_"
NAVER_CLIENT_SECRET = "jdr3EuEGKg"
GOOGLE_API_KEY = "AIzaSyDF2PjlBkUupABpDhmte4xXfdWH0kLTaUk"


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


def fetch_naver_images(place_name):
    url = "https://openapi.naver.com/v1/search/image"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": place_name, "display": 1}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        items = response.json().get('items', [])
        if items:
            return items[0]['link']
    return "https://via.placeholder.com/150"


def fetch_naver_reviews(place_name):
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": place_name, "display": 10}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        items = response.json().get('items', [])
        reviews = [{"description": item['description'], "link": item['link']} for item in items]
        return reviews
    return []


def filter_reviews(reviews):
    ad_keywords = ["광고", "홍보", "할인", "이용권", "협찬", "제휴"]
    filtered_reviews = [review for review in reviews if not any(keyword in review["description"] for keyword in ad_keywords)]
    return filtered_reviews


def kakao_map_iframe(lat, lon, places):
    iframe_url = f"https://map.kakao.com/?urlLevel=3&map_type=TYPE_MAP&urlx={lon}&urly={lat}&map_attribute=ROADMAP"
    iframe_html = f"""
    <iframe width="100%" height="700" src="{iframe_url}" frameborder="0"></iframe>
    """
    return iframe_html


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
    map_html = kakao_map_iframe(lat, lon, restaurants)
    html(map_html, height=700, scrolling=True)

    st.markdown("<h3 style='margin-top: 20px;'>주변 음식점 목록:</h3>", unsafe_allow_html=True)
    st.markdown("<div class='restaurant-container' style='display: flex; flex-wrap: wrap; gap: 20px; justify-content: space-between; width: 100%;'>", unsafe_allow_html=True)
    for restaurant in restaurants:
        naver_image = fetch_naver_images(restaurant['place_name'])
        reviews = fetch_naver_reviews(restaurant['place_name'])
        filtered_reviews = filter_reviews(reviews)

        st.markdown(f"""
<div class="card" style="flex: 1 1 calc(48% - 20px); margin-bottom: 20px; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);">
    <img src="{naver_image}" class="card-img-top" alt="{restaurant['place_name']}" style="border-radius: 10px 10px 0 0; width: 100%; height: auto;">
    <div class="card-body">
        <h4 class="card-title" style="font-weight: bold; color: #007BFF;">{restaurant['place_name']}</h4>
        <p class="card-text"><strong>주소:</strong> {restaurant['road_address_name']}</p>
        <p class="card-text"><strong>전화번호:</strong> {restaurant['phone']}</p>
        <p class="card-text"><strong>광고 없는 후기:</strong></p>
        <ul>
            {''.join([f'<li>{review["description"]} <a href="{review["link"]}" target="_blank" style="color: #007BFF; text-decoration: underline;">후기 자세히 보기</a></li>' for review in filtered_reviews[:3]])}
        </ul>
        <details>
            <summary>후기 더보기</summary>
            <ul>
                {''.join([f'<li>{review["description"]} <a href="{review["link"]}" target="_blank" style="color: #007BFF; text-decoration: underline;">후기 자세히 보기</a></li>' for review in filtered_reviews[3:]])}
            </ul>
        </details>
        <div style="margin-top: 20px;">
            <a href="{restaurant['place_url']}" target="_blank" style="text-decoration: none; background-color: #007BFF; color: white; padding: 10px 15px; border-radius: 5px;">(KAKAO)음식점 정보</a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.write("음식점을 찾을 수 없습니다.")


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
        .restaurant-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: space-between;
            width: 100%;
        }
        .card {
            flex: 1 1 calc(48% - 20px);
            margin-bottom: 20px;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
        }
        .card-body {
            padding: 10px;
        }
        .card-title {
            font-weight: bold;
            color: #007BFF;
        }
        .card-text {
            margin-bottom: 10px;
        }
        .btn-primary {
            text-decoration: none;
            background-color: #007BFF;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
        }
        .btn-primary:hover {
            background-color: #0056b3;
        }
    </style>
""", unsafe_allow_html=True)
