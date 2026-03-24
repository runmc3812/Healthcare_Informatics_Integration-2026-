# 📊 4주차 실습 — 데이터 전처리 + 기초 시각화

**의료정보융합실무** | 보건의료정보학과 장진수 교수

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/YOUR_REPO/blob/main/week4_실습.ipynb)

---

## 🗺️ 실습 내용

| 단계 | 내용 |
|:---:|---|
| STEP 0 | 환경 준비 (한글 폰트) |
| STEP 1 | 데이터 불러오기 + `df.head()` |
| STEP 2 | 결측치·이상치 탐색 (`df.info()`, `df.describe()`) |
| STEP 3 | 결측치 처리 (`dropna`, `fillna`) |
| STEP 4 | 이상치 처리 (조건 필터링) |
| STEP 5 | 히스토그램 — 분포 확인 |
| STEP 6 | 산점도 — 두 변수 관계 |
| STEP 7 | 막대그래프 — 범주별 비교 |
| STEP 8 | ✏️ 직접 해보기 (응용 과제) |

---

## 🚀 실습 시작 방법

### 방법 1 — Colab 버튼 클릭 (권장)
위의 **Open In Colab** 배지 클릭 → 구글 계정 로그인 → 바로 실행

### 방법 2 — 직접 URL 입력
```
https://colab.research.google.com/github/YOUR_USERNAME/YOUR_REPO/blob/main/week4_실습.ipynb
```

> ⚠️ `YOUR_USERNAME` / `YOUR_REPO` 를 실제 GitHub 계정명·저장소명으로 바꾸세요

---

## 📁 파일 구조

```
.
├── week4_실습.ipynb       ← Colab 실습 노트북 (메인)
├── health_survey.csv      ← 대학생 건강설문 데이터 (50명, 결측치·이상치 포함)
└── README.md
```

---

## 📋 데이터 변수 설명 (`health_survey.csv`)

| 변수 | 유형 | 설명 | 이상치 기준 |
|---|---|---|---|
| ID | 식별자 | 학생 고유번호 | — |
| 성별 | 범주형 | 남 / 여 | — |
| 나이 | 연속형 | 만 나이 | 18~40세 |
| 학년 | 범주형 | 1~4학년 | — |
| 수면시간(h) | 연속형 | 하루 평균 수면 | 3~24시간 |
| BMI | 연속형 | 체질량지수 | 10~50 |
| PHQ9점수 | 연속형 | 우울 선별 척도 | 0~27 |
| 스마트폰(h) | 연속형 | 하루 스마트폰 사용 | — |
| 운동여부 | 범주형 | 예 / 아니오 | — |
| 흡연여부 | 범주형 | 흡연 / 비흡연 | — |
| 음주여부 | 범주형 | 음주 / 비음주 | — |
| 스트레스점수 | 연속형 | 자가보고 스트레스 | 0~40 |
| 카페인(mg) | 연속형 | 하루 카페인 섭취 | — |
| 거주지역 | 범주형 | 서울/경기/부산 등 | — |

> ⚠️ 이 데이터에는 **결측치(빈칸)** 와 **이상치(비정상 값)** 가 고의로 포함되어 있습니다

---

## 🛠️ 사용 라이브러리

별도 설치 없이 **Google Colab** 에서 바로 실행 가능합니다 (pandas, matplotlib, seaborn 기본 탑재).

---

*의료정보융합실무 4주차 | 보건의료정보학과*
