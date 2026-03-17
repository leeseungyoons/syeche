import os
import re
import math
import html
from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st


st.set_page_config(
    page_title="광고 없는 찐맛집 추천 앱",
    page_icon="🍽️",
    layout="wide",
)


# =========================================================
# Secrets / Env
# =========================================================
def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, default)


KAKAO_REST_API_KEY = get_secret("KAKAO_REST_API_KEY")
NAVER_CLIENT_ID = get_secret("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = get_secret("NAVER_CLIENT_SECRET")


# =========================================================
# Utils
# =========================================================
def esc(text: Optional[str]) -> str:
    return html.escape(text or "")


def strip_html_tags(text: str) -> str:
    return re.sub(r"<.*?>", "", text or "")


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    r = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(r * c)


def build_score(filtered_review_count: int, distance_m: int) -> float:
    return round(filtered_review_count * 10 - (distance_m / 100), 2)


def ensure_keys() -> bool:
    missing = []
    if not KAKAO_REST_API_KEY:
        missing.append("KAKAO_REST_API_KEY")
    if not NAVER_CLIENT_ID:
        missing.append("NAVER_CLIENT_ID")
    if not NAVER_CLIENT_SECRET:
        missing.append("NAVER_CLIENT_SECRET")

    if missing:
        st.error("필수 키가 부족해: " + ", ".join(missing))
        st.code(
            '''KAKAO_REST_API_KEY = "여기에_카카오_REST_API_KEY"
NAVER_CLIENT_ID = "여기에_네이버_CLIENT_ID"
NAVER_CLIENT_SECRET = "여기에_네이버_CLIENT_SECRET"''',
            language="toml",
        )
        return False
    return True


def has_naver_keys() -> bool:
    return bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET)


# =========================================================
# API wrappers
# =========================================================
def kakao_get(url: str, params: Dict) -> Tuple[int, Dict]:
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    response = requests.get(url, headers=headers, params=params, timeout=15)

    try:
        payload = response.json()
    except Exception:
        payload = {"raw_text": response.text}

    return response.status_code, payload


def naver_get(url: str, params: Dict) -> Tuple[int, Dict]:
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    response = requests.get(url, headers=headers, params=params, timeout=15)

    try:
        payload = response.json()
    except Exception:
        payload = {"raw_text": response.text}

    return response.status_code, payload


# =========================================================
# Kakao location search
# =========================================================
def kakao_address_to_coords(address: str) -> Tuple[Optional[float], Optional[float], Optional[str], Dict]:
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    params = {"query": address}

    status, payload = kakao_get(url, params)
    debug = {
        "step": "address_search",
        "query": address,
        "status": status,
        "payload": payload,
    }

    if status == 200:
        docs = payload.get("documents", [])
        if docs:
            doc = docs[0]
            lat = float(doc["y"])
            lon = float(doc["x"])
            label = doc.get("address_name") or address
            return lat, lon, label, debug

    return None, None, None, debug


def kakao_keyword_to_coords(query: str) -> Tuple[Optional[float], Optional[float], Optional[str], Dict]:
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": query, "size": 1}

    status, payload = kakao_get(url, params)
    debug = {
        "step": "keyword_search",
        "query": query,
        "status": status,
        "payload": payload,
    }

    if status == 200:
        docs = payload.get("documents", [])
        if docs:
            doc = docs[0]
            lat = float(doc["y"])
            lon = float(doc["x"])
            label = doc.get("place_name") or query
            return lat, lon, label, debug

    return None, None, None, debug


def resolve_location(query: str) -> Tuple[Optional[float], Optional[float], Optional[str], List[Dict]]:
    logs: List[Dict] = []

    lat, lon, label, debug = kakao_address_to_coords(query)
    logs.append(debug)
    if lat is not None and lon is not None:
        return lat, lon, label, logs

    lat, lon, label, debug = kakao_keyword_to_coords(query)
    logs.append(debug)
    if lat is not None and lon is not None:
        return lat, lon, label, logs

    return None, None, None, logs


# =========================================================
# Kakao nearby restaurant search
# =========================================================
def kakao_search_restaurants(lat: float, lon: float, radius: int, size: int) -> Tuple[List[Dict], Dict]:
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    collected: List[Dict] = []
    debug: Dict = {"pages": []}

    page = 1
    while len(collected) < size:
        page_size = min(15, size - len(collected))
        params = {
            "category_group_code": "FD6",
            "x": lon,
            "y": lat,
            "radius": radius,
            "sort": "distance",
            "page": page,
            "size": page_size,
        }

        status, payload = kakao_get(url, params)
        debug["pages"].append(
            {
                "page": page,
                "status": status,
                "meta": payload.get("meta", {}),
                "sample_payload": payload if page == 1 else {"documents_count": len(payload.get("documents", []))},
            }
        )

        if status != 200:
            debug["error"] = payload
            break

        docs = payload.get("documents", [])
        if not docs:
            break

        collected.extend(docs)

        meta = payload.get("meta", {})
        if meta.get("is_end", True):
            break

        page += 1

    return collected[:size], debug


# =========================================================
# Naver APIs
# =========================================================
def naver_search_image(place_name: str) -> str:
    if not has_naver_keys():
        return "https://via.placeholder.com/600x400?text=No+Image"

    url = "https://openapi.naver.com/v1/search/image"
    params = {"query": place_name, "display": 1, "sort": "sim"}

    try:
        status, payload = naver_get(url, params)
        if status == 200:
            items = payload.get("items", [])
            if items:
                return items[0].get("link", "https://via.placeholder.com/600x400?text=No+Image")
    except Exception:
        pass

    return "https://via.placeholder.com/600x400?text=No+Image"


def naver_search_blog_reviews(place_name: str, display: int = 10) -> List[Dict]:
    if not has_naver_keys():
        return []

    url = "https://openapi.naver.com/v1/search/blog.json"
    params = {"query": place_name, "display": display, "sort": "sim"}

    try:
        status, payload = naver_get(url, params)
        if status == 200:
            items = payload.get("items", [])
            results = []
            for item in items:
                results.append(
                    {
                        "title": strip_html_tags(item.get("title", "")),
                        "description": strip_html_tags(item.get("description", "")),
                        "link": item.get("link", "#"),
                    }
                )
            return results
    except Exception:
        pass

    return []


def filter_ad_reviews(reviews: List[Dict]) -> List[Dict]:
    ad_keywords = [
        "광고", "홍보", "협찬", "제휴", "체험단", "원고료", "소정의", "제공받아",
        "방문권", "이용권", "서포터즈", "파트너스", "업체", "지원받아", "할인",
    ]

    filtered = []
    for review in reviews:
        merged = f"{review.get('title', '')} {review.get('description', '')}".lower()
        if not any(keyword in merged for keyword in ad_keywords):
            filtered.append(review)
    return filtered


# =========================================================
# Data enrich
# =========================================================
def enrich_places(base_lat: float, base_lon: float, places: List[Dict]) -> List[Dict]:
    enriched = []

    for place in places:
        try:
            lat = float(place["y"])
            lon = float(place["x"])
        except Exception:
            lat, lon = None, None

        distance_m = 0
        if lat is not None and lon is not None:
            distance_m = haversine_distance_m(base_lat, base_lon, lat, lon)

        place_name = place.get("place_name", "이름 없음")
        raw_reviews = naver_search_blog_reviews(place_name, display=10)
        filtered_reviews = filter_ad_reviews(raw_reviews)
        image_url = naver_search_image(place_name)

        enriched.append(
            {
                "id": f"{place.get('id', '')}_{place_name}",
                "place_name": place_name,
                "category_name": place.get("category_name", "음식점"),
                "road_address_name": place.get("road_address_name") or place.get("address_name") or "주소 정보 없음",
                "phone": place.get("phone") or "전화번호 없음",
                "place_url": place.get("place_url", "#"),
                "distance_m": distance_m,
                "image_url": image_url,
                "raw_reviews": raw_reviews,
                "filtered_reviews": filtered_reviews,
                "filtered_review_count": len(filtered_reviews),
                "score": build_score(len(filtered_reviews), distance_m),
            }
        )

    return enriched


# =========================================================
# Session state
# =========================================================
if "results" not in st.session_state:
    st.session_state.results = []

if "saved_places" not in st.session_state:
    st.session_state.saved_places = []

if "search_center" not in st.session_state:
    st.session_state.search_center = None

if "last_query" not in st.session_state:
    st.session_state.last_query = ""

if "resolve_logs" not in st.session_state:
    st.session_state.resolve_logs = []

if "restaurant_logs" not in st.session_state:
    st.session_state.restaurant_logs = {}


# =========================================================
# Save helpers
# =========================================================
def save_place(item: Dict) -> None:
    existing_ids = {x["id"] for x in st.session_state.saved_places}
    if item["id"] not in existing_ids:
        st.session_state.saved_places.append(item)


def remove_saved_place(item_id: str) -> None:
    st.session_state.saved_places = [x for x in st.session_state.saved_places if x["id"] != item_id]


# =========================================================
# UI styles
# =========================================================
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-text {
        color: #94a3b8;
        margin-bottom: 1rem;
    }
    .chip {
        display: inline-block;
        padding: 0.22rem 0.6rem;
        border-radius: 999px;
        background: #1e293b;
        color: #e2e8f0;
        font-size: 0.8rem;
        margin-right: 0.3rem;
        margin-bottom: 0.35rem;
    }
    .review-box {
        padding: 10px 12px;
        border-radius: 12px;
        background: rgba(148,163,184,0.08);
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🍽️ 광고 없는 찐맛집 추천 앱</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-text">카카오 로컬 검색으로 위치와 주변 음식점을 찾고, 네이버 블로그 후기에서 광고성 글을 최대한 걸러 찐맛집 후보를 추천합니다.</div>',
    unsafe_allow_html=True,
)

if not ensure_keys():
    st.stop()


# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.header("검색 옵션")
    radius = st.slider("검색 반경 (m)", 500, 5000, 2000, 100)
    size = st.slider("최대 검색 개수", 5, 15, 10, 1)
    sort_by = st.selectbox("정렬 기준", ["추천순", "광고 제거 후기 많은 순", "거리순", "이름순"])
    min_filtered_reviews = st.slider("최소 광고 제거 후기 수", 0, 10, 1, 1)
    only_with_phone = st.toggle("전화번호 있는 곳만 보기", value=False)
    debug_mode = st.toggle("진단 정보 보기", value=True)

    st.divider()
    st.metric("저장한 맛집", len(st.session_state.saved_places))


# =========================================================
# Main input
# =========================================================
query = st.text_input(
    "주소 또는 지역명을 입력해줘",
    value=st.session_state.last_query,
    placeholder="예: 동탄역 / 경기도 화성시 동탄역로 151 / 성수동 / 강남역",
)

col1, col2 = st.columns([5, 1])

with col1:
    search_clicked = st.button("🔍 그 근처 찐맛집 찾기", use_container_width=True)

with col2:
    reset_clicked = st.button("초기화", use_container_width=True)

if reset_clicked:
    st.session_state.results = []
    st.session_state.search_center = None
    st.session_state.last_query = ""
    st.session_state.resolve_logs = []
    st.session_state.restaurant_logs = {}
    st.rerun()


# =========================================================
# Search action
# =========================================================
if search_clicked:
    if not query.strip():
        st.warning("주소나 지역명을 먼저 입력해줘.")
    else:
        st.session_state.last_query = query.strip()

        with st.spinner("위치와 주변 음식점을 찾는 중..."):
            lat, lon, label, resolve_logs = resolve_location(query.strip())
            st.session_state.resolve_logs = resolve_logs

            if lat is None or lon is None:
                st.session_state.results = []
                st.session_state.search_center = None
                st.error("위치를 찾지 못했어. 더 자세한 주소나 지역명으로 다시 입력해줘.")
            else:
                raw_places, restaurant_logs = kakao_search_restaurants(lat, lon, radius=radius, size=size)
                st.session_state.restaurant_logs = restaurant_logs

                enriched = enrich_places(lat, lon, raw_places)

                filtered = []
                for item in enriched:
                    if only_with_phone and item["phone"] == "전화번호 없음":
                        continue
                    if item["filtered_review_count"] < min_filtered_reviews:
                        continue
                    filtered.append(item)

                if sort_by == "추천순":
                    filtered = sorted(filtered, key=lambda x: x["score"], reverse=True)
                elif sort_by == "광고 제거 후기 많은 순":
                    filtered = sorted(filtered, key=lambda x: x["filtered_review_count"], reverse=True)
                elif sort_by == "거리순":
                    filtered = sorted(filtered, key=lambda x: x["distance_m"])
                else:
                    filtered = sorted(filtered, key=lambda x: x["place_name"])

                st.session_state.results = filtered
                st.session_state.search_center = {"lat": lat, "lon": lon, "label": label or query.strip()}


# =========================================================
# Tabs
# =========================================================
tab1, tab2, tab3 = st.tabs(["추천 결과", "저장한 맛집", "진단 정보"])

with tab1:
    center = st.session_state.search_center
    results = st.session_state.results

    if center:
        st.caption(f"검색 기준 위치: {center['label']}")

    m1, m2, m3 = st.columns(3)
    m1.metric("추천 결과", len(results))
    m2.metric("최소 광고 제거 후기 수", min_filtered_reviews)
    m3.metric("검색 반경", f"{radius}m")

    st.divider()

    if not results:
        st.info("아직 결과가 없어. 주소나 지역명을 입력하고 검색해봐.")
    else:
        for item in results:
            with st.container(border=True):
                top1, top2 = st.columns([4, 1])

                with top1:
                    st.subheader(f"🍴 {item['place_name']}")
                    st.markdown(
                        f'<span class="chip">거리 {item["distance_m"]}m</span>'
                        f'<span class="chip">광고 제거 후기 {item["filtered_review_count"]}개</span>'
                        f'<span class="chip">추천점수 {item["score"]}</span>',
                        unsafe_allow_html=True,
                    )
                    st.write(f"**주소:** {item['road_address_name']}")
                    st.write(f"**전화번호:** {item['phone']}")
                    st.write(f"**카테고리:** {item['category_name']}")

                with top2:
                    if st.button("저장", key=f"save_{item['id']}", use_container_width=True):
                        save_place(item)
                        st.success("저장 완료")
                        st.rerun()

                img_col, review_col = st.columns([1.05, 1.45])

                with img_col:
                    st.image(item["image_url"], use_container_width=True)

                with review_col:
                    st.markdown("**광고 제거 후기 미리보기**")
                    if item["filtered_reviews"]:
                        for review in item["filtered_reviews"][:3]:
                            st.markdown(
                                f"""
                                <div class="review-box">
                                    <b>{esc(review["title"])}</b><br>
                                    {esc(review["description"])}<br>
                                    <a href="{review["link"]}" target="_blank">후기 보기</a>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("광고 제거 후 남은 후기가 없어.")

                st.link_button("카카오맵에서 보기", item["place_url"], use_container_width=True)

with tab2:
    saved = st.session_state.saved_places

    if not saved:
        st.info("저장한 맛집이 아직 없어.")
    else:
        for item in saved:
            with st.container(border=True):
                st.subheader(f"⭐ {item['place_name']}")
                st.write(f"**주소:** {item['road_address_name']}")
                st.write(f"**전화번호:** {item['phone']}")
                st.write(f"**광고 제거 후기 수:** {item['filtered_review_count']}개")

                c1, c2 = st.columns(2)
                with c1:
                    st.link_button(
                        "카카오맵에서 보기",
                        item["place_url"],
                        key=f"saved_link_{item['id']}",
                        use_container_width=True,
                    )
                with c2:
                    if st.button("저장 해제", key=f"remove_{item['id']}", use_container_width=True):
                        remove_saved_place(item["id"])
                        st.success("삭제 완료")
                        st.rerun()

with tab3:
    if debug_mode:
        st.subheader("위치 찾기 로그")
        st.json(st.session_state.resolve_logs)

        st.subheader("주변 음식점 검색 로그")
        st.json(st.session_state.restaurant_logs)

        st.subheader("현재 키 상태")
        st.json(
            {
                "KAKAO_REST_API_KEY_exists": bool(KAKAO_REST_API_KEY),
                "NAVER_CLIENT_ID_exists": bool(NAVER_CLIENT_ID),
                "NAVER_CLIENT_SECRET_exists": bool(NAVER_CLIENT_SECRET),
            }
        )
    else:
        st.info("사이드바에서 '진단 정보 보기'를 켜면 여기서 응답 로그를 볼 수 있어.")
