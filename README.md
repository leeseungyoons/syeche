# 광고 없는 찐맛집 추천 앱

링크 : https://ad-free-restaurant-recommender-852w5tmecg9lbztbowwabt.streamlit.app/

카카오 로컬 API와 네이버 검색 API를 활용해 **주변 음식점을 찾고**, **광고성 블로그 후기를 최대한 걸러낸 뒤**, **거리·후기 수·후기 신뢰도 기반 점수**로 맛집 후보를 추천하는 Streamlit 웹앱입니다.

## 프로젝트 소개
이 프로젝트는 단순히 "근처 음식점 목록"을 보여주는 데서 끝나지 않고,
실제 사용자가 참고할 만한 **광고 제거 후기 기반 추천 결과**를 제공하는 데 초점을 맞췄습니다.

사용자는 `동탄역`, `강남역`, `성수동`, `경기도 화성시 동탄역로 151` 같은 위치를 입력하고,
검색 반경·정렬 기준·최소 후기 수 같은 옵션을 조절해 원하는 맛집 후보를 빠르게 찾을 수 있습니다.

## 주요 기능
- **위치 검색**
  - 카카오 주소 검색 / 키워드 검색을 조합해 검색 위치를 찾습니다.
  - 입력값이 주소형인지, 역/장소명인지에 따라 우선 검색 방식을 다르게 적용합니다.

- **주변 음식점 탐색**
  - 카카오 카테고리 검색(`FD6`)으로 주변 음식점을 불러옵니다.
  - 반경 밖 결과를 제외하고, 중복 장소를 제거합니다.

- **광고성 후기 필터링**
  - 네이버 블로그 검색 결과를 기반으로 후기 후보를 수집합니다.
  - `광고`, `협찬`, `체험단`, `제공받아`, `원고료` 등 광고성 키워드를 제거합니다.
  - 가게명/주소 관련성이 낮은 후기 역시 제외합니다.

- **추천 점수 계산**
  - 광고 제거 후기 수
  - 검색 위치와의 거리
  - 원본 후기 대비 광고 제거 후 남은 비율
  
  위 요소를 조합해 0~100점 범위의 추천 점수를 계산합니다.

- **결과 저장 기능**
  - 마음에 드는 맛집을 저장해 따로 모아볼 수 있습니다.

- **진단 정보 확인**
  - 위치 검색 로그
  - 주변 음식점 검색 로그
  - 현재 API 키 인식 여부
  
  를 앱 안에서 바로 확인할 수 있어 디버깅에 유리합니다.

## 기술 스택
- **Python**
- **Streamlit**
- **Kakao Local API**
- **Naver Search API (Blog / Image)**
- **Requests**

## 파일 구조
```bash
.
├── chan.py
├── requirements.txt
└── .streamlit/
    └── secrets.toml   # 로컬 실행용 (GitHub 업로드 금지)
```

## 실행 화면 흐름
1. 주소 또는 지역명 입력
2. 검색 반경 / 정렬 기준 / 최소 후기 수 설정
3. 주변 음식점 조회
4. 광고 제거 후기 기반 추천 결과 확인
5. 저장하거나 카카오맵 링크로 상세 확인

## 추천 점수 기준
추천 점수는 아래 요소를 기반으로 계산됩니다.

- **후기 수 반영**: 광고 제거 후 남은 후기 개수가 많을수록 가점
- **거리 반영**: 검색 기준 위치와 가까울수록 가점
- **신뢰도 반영**: 원본 후기 중 광고 제거 후 남은 비율이 높을수록 가점

즉, 단순히 후기가 많다고 높은 점수를 주는 것이 아니라,
**가까우면서도 광고성 비중이 상대적으로 낮은 곳**이 더 높은 점수를 받도록 설계했습니다.

## 광고 제거 기준
다음과 같은 표현이 포함된 후기는 광고성일 가능성이 높다고 보고 제외합니다.

- 광고
- 협찬
- 체험단
- 원고료
- 소정의
- 제공받아 / 지원받아
- 무료시식
- sponsored / paid 등

또한 가게명, 지역명과의 관련성이 낮은 후기 역시 필터링합니다.

## 설치 방법
### 1) 저장소 클론
```bash
git clone https://github.com/your-username/ad-free-restaurant-recommender.git
cd ad-free-restaurant-recommender
```

### 2) 패키지 설치
```bash
pip install -r requirements.txt
```

### 3) 로컬 secrets 파일 생성
프로젝트 루트에 `.streamlit/secrets.toml` 파일을 만들고 아래 내용을 입력합니다.

```toml
KAKAO_REST_API_KEY = "YOUR_KAKAO_REST_API_KEY"
NAVER_CLIENT_ID = "YOUR_NAVER_CLIENT_ID"
NAVER_CLIENT_SECRET = "YOUR_NAVER_CLIENT_SECRET"
```

## 로컬 실행
```bash
streamlit run chan.py
```

## Streamlit Cloud 배포
이 프로젝트는 Streamlit Community Cloud에 바로 배포할 수 있습니다.

### 배포 순서
1. `chan.py`, `requirements.txt`, `.gitignore`, `README.md`를 GitHub에 push
2. Streamlit Community Cloud에서 **Create app** 선택
3. GitHub 저장소 선택
4. **Main file path**를 `chan.py`로 지정
5. **Secrets** 칸에 아래 내용을 붙여넣기

```toml
KAKAO_REST_API_KEY = "YOUR_KAKAO_REST_API_KEY"
NAVER_CLIENT_ID = "YOUR_NAVER_CLIENT_ID"
NAVER_CLIENT_SECRET = "YOUR_NAVER_CLIENT_SECRET"
```

### 주의
`secrets.toml` 파일 자체를 GitHub에 올리면 안 됩니다.
반드시 `.gitignore`에 아래 내용을 추가하세요.

```gitignore
.streamlit/secrets.toml
```

## 환경 변수 / API 키
### Kakao
- REST API Key 필요
- 카카오맵/로컬 서비스 사용 설정 필요

### Naver
- Client ID
- Client Secret

둘 다 정상 설정되어야 앱이 제대로 동작합니다.

## 한계점
- 네이버 블로그 검색 결과 기반이라 후기 품질은 검색 결과에 영향을 받습니다.
- 이미지 검색은 참고용이며 실제 매장 대표 이미지와 다를 수 있습니다.
- 광고성 글을 최대한 줄이도록 설계했지만, 100% 완벽한 광고 판별은 아닙니다.

## 개선 아이디어
- 후기 본문 감성 분석 추가
- 별점/평점 데이터 결합
- 지도 시각화 추가
- 가게별 상세 페이지 구성
- 사용자 선호 카테고리 기반 추천
- 리뷰 텍스트 임베딩 기반 더 정교한 관련성 필터링

## 프로젝트 목적
이 프로젝트는 **지도 API 활용**, **검색 기반 데이터 수집**, **광고성 후기 필터링**, **추천 로직 설계**, **Streamlit 배포 경험**을 하나의 서비스 형태로 구현하는 것을 목표로 했습니다.

즉, 단순한 맛집 검색 앱이 아니라,
**실사용 가능한 데이터 기반 추천 앱**을 만드는 데 초점을 둔 프로젝트입니다.

---

**광고를 줄이고, 실제 후기 기반으로 더 믿을 만한 맛집 후보를 찾는 앱**
