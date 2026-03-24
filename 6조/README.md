# 의료인력 KOSIS 분석 · Colab 실행 패키지

이 폴더는 **KOSIS CSV 4개**를 이용해
**인구구조 변화, 수도권 인구집중, 지역별 의사밀도**를 분석하는 GitHub + Colab 실행 패키지입니다.

## 폴더 구조

```text
medical_workforce_kosis/
├─ data/
│  ├─ 고령인구비율_시도_시_군_구__20260324171859.csv
│  ├─ 순이동인구_시도_시_군_구__20260324172019.csv
│  ├─ 주민등록인구_시도_시_군_구__20260324172055.csv
│  └─ 인구_천명당_의료기관_종사_의사수_시도_시_군_구__20260324172132.csv
├─ notebooks/
│  └─ medical_workforce_kosis_colab.ipynb
├─ src/
│  └─ medical_workforce_kosis_analysis.py
└─ README.md
```

## GitHub 업로드 위치 추천

이전 대화에서 사용한 저장소를 그대로 쓴다면 아래 경로가 가장 편합니다.

```text
Healthcare_Informatics_Integration-2026-/
└─ 1조/
   └─ medical_workforce_kosis/
```

즉, 이 폴더 전체를 **`1조/medical_workforce_kosis/`** 로 업로드하면 됩니다.

## Colab 실행 링크 형식

저장소와 경로가 아래와 같다면,
- GitHub 사용자: `runmc3812`
- 저장소: `Healthcare_Informatics_Integration-2026-`
- 브랜치: `main`
- 폴더: `1조/medical_workforce_kosis`

Colab 링크는 아래 형식입니다.

```text
https://colab.research.google.com/github/runmc3812/Healthcare_Informatics_Integration-2026-/blob/main/1%EC%A1%B0/medical_workforce_kosis/notebooks/medical_workforce_kosis_colab.ipynb
```

## 실행 결과

실행이 완료되면 아래가 자동 생성됩니다.
- 패널데이터 CSV
- 상관분석 / 회귀분석 결과 CSV
- HTML/PNG 그래프 다수
- 전체 결과 ZIP 파일

## 기본 그래프

- 전국 평균 지수 추세
- 시도별 의사밀도 스몰멀티플
- 시도×연도 의사밀도 히트맵
- 고령인구비율 vs 의사밀도 산점도
- 순이동률 vs 의사밀도 버블차트
- 수도권 vs 비수도권 박스플롯
- 슬로프그래프
- 범프차트
- 사분면 그래프
- 변화율 막대그래프
- 상관행렬 히트맵
- 최신 연도 시도별 순위 막대그래프

## 주의

다른 저장소/경로에 올릴 경우에는 노트북 첫 코드셀의 `GITHUB_USER`, `REPO_NAME`, `BRANCH`, `BASE_PATH`만 수정하면 됩니다.
