# Thyroid cancer incidence policy analysis (GitHub + Colab)

이 저장소는 **갑상선암 검진 정책 변화 이후 국내 갑상선암 발생 패턴**을 Google Colab에서 재현 가능하게 분석하기 위한 구성입니다.

## 권장 구조

```text
repo/
├─ notebooks/
│  └─ thyroid_policy_analysis_colab.ipynb
├─ src/
│  └─ thyroid_colab_analysis.py
├─ data/
│  ├─ 국립암센터_24개종 암발생률_20260120.csv
│  └─ 24개_암종_성_연령_5세_별_암발생자수__발생률_20260324142549.csv
└─ requirements.txt
```

## 사용 방법

1. 저장소를 public으로 둡니다.
2. CSV 두 개를 `data/` 폴더에 넣습니다.
3. 노트북 상단에서 `GITHUB_USER`, `REPO_NAME`, `BRANCH`만 수정합니다.
4. Colab에서 GitHub notebook을 열어 실행합니다.

## 데이터 연결 순서

1. GitHub raw URL
2. Colab 업로드 fallback

## 주요 출력물

- 전체/남녀 ASR 추세
- 2012=100 충격지수
- 버터플라이 3단 비교
- 연령 heatmap
- 감소율/반등 워터폴
- 버블차트
- ITS 계수표 및 적합 그래프
- 자동 해석 요약
