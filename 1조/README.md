# Thyroid cancer incidence policy analysis (1-click Colab)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/runmc3812/Healthcare_Informatics_Integration-2026-/blob/main/1%EC%A1%B0/notebooks/thyroid_policy_analysis_colab.ipynb)

이 노트북은 학생들이 **Colab 링크만 열고 코드 셀의 플레이 버튼 1번만 누르면** 바로 분석이 돌아가도록 맞춘 버전입니다.

## 저장소 구조
```text
1조/
├─ data/
│  ├─ 국립암센터_24개종 암발생률_20260120.csv
│  └─ 24개_암종_성_연령_5세_별_암발생자수__발생률_20260324142549.csv
├─ notebooks/
│  └─ thyroid_policy_analysis_colab.ipynb
├─ src/
│  └─ thyroid_colab_analysis.py
├─ README.md
└─ requirements.txt
```

## 중요한 점
- 노트북 안에 저장소 경로가 이미 고정되어 있어 별도 수정이 필요 없습니다.
- `1조/` 하위 경로를 포함한 raw URL을 자동으로 생성합니다.
- CSV와 스크립트는 GitHub raw에서 직접 불러옵니다.
- 결과는 `thyroid_analysis_outputs.zip`으로 자동 다운로드됩니다.
