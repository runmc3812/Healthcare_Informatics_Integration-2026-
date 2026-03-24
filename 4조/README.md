# 🚭 바이오마커 기반 흡연 여부 예측 모델

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/runmc3812/Healthcare_Informatics_Integration-2026-/4조/blob/main/smoker_biosignal_analysis.ipynb)
[![Kaggle](https://img.shields.io/badge/Data-Kaggle-20BEFF?logo=kaggle)](https://www.kaggle.com/competitions/playground-series-s3e24)

> 혈액·신체 검사 수치(바이오마커)만으로 흡연 여부를 예측하고,  
> 어떤 지표가 핵심인지 **SHAP**으로 해석한다.

---

## 📐 연구 설계

| 구분 | 내용 |
|---|---|
| **데이터** | Kaggle Playground Series S3E24 (159,256명) |
| **독립변수 (X)** | 27개 바이오마커 — 신체측정, 혈압, 혈액검사, 간기능 등 |
| **종속변수 (y)** | 흡연 여부 (0 = 비흡연, 1 = 흡연) |
| **분석 방법** | 로지스틱 회귀 (오즈비 해석) + Random Forest (성능) + SHAP (설명) |
| **평가 지표** | AUC-ROC, F1-score, 5-Fold Cross Validation |

### 💡 연구 가설

| 가설 | 내용 |
|---|---|
| H1 | GTP(γ-GTP), 헤모글로빈, 중성지방은 흡연자에서 유의미하게 높을 것이다 |
| H2 | 바이오마커만으로 흡연 여부를 **AUC 0.80 이상** 예측할 수 있다 |
| H3 | Random Forest가 로지스틱 회귀보다 높은 예측 성능을 보일 것이다 |

---

## 📁 파일 구조

```
.
├── smoker_biosignal_analysis.ipynb   # 메인 분석 노트북 (Colab 실행)
├── README.md
└── outputs/                          # 실행 후 자동 생성
    ├── eda_biomarker.png             # 집단 간 분포 비교
    ├── eda_heatmap.png               # 상관관계 히트맵
    ├── lr_odds_ratio.png             # 로지스틱 오즈비
    ├── rf_feature_importance.png     # RF 변수 중요도
    ├── shap_beeswarm.png             # SHAP Beeswarm
    ├── shap_bar.png                  # SHAP 변수 중요도 Bar
    └── roc_cm.png                    # ROC 커브 + 혼동행렬
```

---

## 🚀 실행 방법

### 1. Colab에서 바로 열기
위의 **Open In Colab** 버튼 클릭

### 2. Kaggle 데이터 다운로드
노트북 **Cell 2**에서 두 가지 방법 중 선택:

**방법 A — kaggle.json 업로드 (권장)**
```
1. kaggle.com/settings → Create New Token → kaggle.json 다운로드
2. Cell 2A 실행 → 파일 선택
```

**방법 B — Google Drive**
```python
from google.colab import drive
drive.mount('/content/drive')
DATA_PATH = '/content/drive/MyDrive/train.csv'
```

### 3. 순서대로 셀 실행
`런타임 → 모두 실행` 또는 셀을 위에서부터 순서대로 실행

---

## 📊 분석 흐름

```
Cell 1  환경 설정 (shap 설치, 한글 폰트)
Cell 2  Kaggle 데이터 다운로드
Cell 3  라이브러리 임포트
Cell 4  데이터 로드 및 기본 확인
Cell 5  변수 설계 (6개 그룹 분류)
Cell 6  전처리 (Winsorizing + Train/Test 분할)
Cell 7  EDA — 집단 간 분포 비교 + 평균 비교표
Cell 8  EDA — 상관관계 히트맵
Cell 9  모델 1: 로지스틱 회귀 + 오즈비 시각화
Cell 10 모델 2: Random Forest + Feature Importance
Cell 11 SHAP 해석 (Beeswarm + Bar)
Cell 12 ROC 커브 비교 + 혼동행렬
Cell 13 5-Fold 교차검증 + 최종 요약
```

---

## 🔬 변수 그룹

| 그룹 | 변수 |
|---|---|
| 신체측정 | age, height(cm), weight(kg), waist(cm) |
| 시력/청력 | eyesight(left/right), hearing(left/right) |
| 혈압 | systolic, relaxation |
| 혈액검사 | fasting blood sugar, cholesterol, triglyceride, HDL, LDL, hemoglobin |
| **간기능** | AST, ALT, **Gtp** ← 핵심 가설 변수 |
| 기타 | urine protein, serum creatinine, dental caries |

---

## 🛠️ 사용 기술

![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-F7931E?logo=scikit-learn)
![SHAP](https://img.shields.io/badge/SHAP-XAI-FF6B6B)
![Pandas](https://img.shields.io/badge/Pandas-2.0-150458?logo=pandas)
![Seaborn](https://img.shields.io/badge/Seaborn-0.13-4C72B0)

---

## 📝 보건학적 함의

1. **혈액검사만으로 흡연 스크리닝 가능성** — 자기보고(self-report) 없이도 객관적 지표로 흡연 여부 추정 가능
2. **GTP·헤모글로빈이 핵심 지표** — 흡연이 간 효소 및 산소 운반 능력에 미치는 영향 재확인
3. **정기 건강검진 데이터 활용** — 기존 검진 결과를 보조 스크리닝 도구로 활용하는 근거 제시

---

## ⚠️ 한계

- Kaggle이 생성한 **합성 데이터(synthetic data)**로, 실제 임상 적용에는 검증 필요
- 단면 자료 — 인과관계 추론 불가
- 전자담배 여부, 흡연량, 흡연 기간 등 추가 변수 없음

---
데이터 출처: Kaggle playground-series-s3e24*
