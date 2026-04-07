
# thyroid_colab_analysis.py
# GitHub + Google Colab friendly analysis script for thyroid cancer incidence data

from __future__ import annotations
import os
import re
import math
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict
from urllib.parse import quote

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl
import statsmodels.api as sm

POLICY_YEAR = 2014
PEAK_YEAR = 2012
COMPARE_YEARS = [2012, 2015, 2023]

def setup_korean_font():
    font_candidates = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
    ]
    for font_path in font_candidates:
        if os.path.exists(font_path):
            fm.fontManager.addfont(font_path)
            mpl.rcParams["font.family"] = fm.FontProperties(fname=font_path).get_name()
            break
    mpl.rcParams["axes.unicode_minus"] = False
    mpl.rcParams["figure.dpi"] = 160

def clean_num(x):
    if pd.isna(x):
        return np.nan
    x = str(x).strip().replace(",", "")
    if x in {"", "-", "nan", "None"}:
        return np.nan
    try:
        return float(x)
    except Exception:
        return np.nan

def age_midpoint(age_str):
    s = str(age_str)
    if s == "계":
        return np.nan
    m = re.match(r"(\d+)\-(\d+)세", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return (a + b) / 2
    if "85세이상" in s:
        return 87.5
    return np.nan

def pct_change(a, b):
    if pd.isna(a) or a == 0:
        return np.nan
    return (b - a) / a * 100

def build_raw_url(*parts: str) -> str:
    encoded = "/".join(quote(str(p), safe="") for p in parts)
    return f"https://raw.githubusercontent.com/{encoded}"

def infer_repo_raw(repo_raw_base: Optional[str], filename: str) -> Optional[str]:
    if not repo_raw_base:
        return None
    base = repo_raw_base.rstrip("/")
    return f"{base}/{quote(str(filename), safe='')}"

def read_csv_flex(path_or_url: str, **kwargs) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]
    last_error = None
    for enc in encodings:
        try:
            return pd.read_csv(path_or_url, encoding=enc, **kwargs)
        except Exception as e:
            last_error = e
    raise last_error

def load_main_incidence(source: str) -> pd.DataFrame:
    df = read_csv_flex(source)
    for c in ["발생자수", "조발생률", "연령표준화발생률"]:
        if c in df.columns:
            df[c] = df[c].apply(clean_num)
    if "암종" not in df.columns:
        raise ValueError("주요 발생률 파일에서 '암종' 열을 찾지 못했습니다.")
    df = df[df["암종"].astype(str).str.contains("갑상선", na=False)].copy()
    df = df.sort_values(["성별", "발생연도"]).reset_index(drop=True)
    return df

def load_age_sex_incidence(source: str) -> pd.DataFrame:
    raw = read_csv_flex(source, header=None)
    year_row = raw.iloc[0].astype(str).tolist()
    metric_row = raw.iloc[1].astype(str).tolist()

    new_cols = []
    for i, (y, m) in enumerate(zip(year_row, metric_row)):
        if i < 3:
            new_cols.append(y)
        else:
            metric = "cases" if "발생자수" in m else "rate"
            new_cols.append(f"{y}_{metric}")

    df = raw.iloc[2:].copy()
    df.columns = new_cols
    df = df.rename(columns={"24개 암종별": "암종", "성별": "성별", "연령별": "연령군"})

    id_vars = ["암종", "성별", "연령군"]
    value_vars = [c for c in df.columns if c not in id_vars]

    long_df = df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="year_metric",
        value_name="value"
    )
    long_df["연도"] = long_df["year_metric"].str.extract(r"(\d{4})").astype(int)
    long_df["지표"] = long_df["year_metric"].str.extract(r"_(cases|rate)")
    long_df["value"] = long_df["value"].apply(clean_num)

    long_df = long_df.pivot_table(
        index=["암종", "성별", "연령군", "연도"],
        columns="지표",
        values="value",
        aggfunc="first"
    ).reset_index()

    long_df.columns.name = None
    long_df = long_df.rename(columns={"cases": "발생자수", "rate": "조발생률"})
    long_df["연령중앙값"] = long_df["연령군"].apply(age_midpoint)
    long_df = long_df[long_df["암종"].astype(str).str.contains("갑상선", na=False)].copy()
    
    # --- [수정] 0-4세 제외 및 연령군 순서 강제 고정 ---
    long_df = long_df[long_df["연령군"] != "0-4세"]
    age_order = [
        '계', '5-9세', '10-14세', '15-19세', '20-24세', '25-29세', 
        '30-34세', '35-39세', '40-44세', '45-49세', '50-54세', 
        '55-59세', '60-64세', '65-69세', '70-74세', '75-79세', 
        '80-84세', '85세이상'
    ]
    long_df["연령군"] = pd.Categorical(long_df["연령군"], categories=age_order, ordered=True)
    # ---------------------------------------------------
    
    long_df = long_df.sort_values(["성별", "연령군", "연도"]).reset_index(drop=True)
    return long_df

def prepare_subsets(main_df: pd.DataFrame, age_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    data = {
        "overall": main_df[main_df["성별"] == "남녀전체"].copy(),
        "male": main_df[main_df["성별"] == "남자"].copy(),
        "female": main_df[main_df["성별"] == "여자"].copy(),
        "age_total": age_df[age_df["성별"] == "계"].copy(),
        "age_male": age_df[age_df["성별"] == "남자"].copy(),
        "age_female": age_df[age_df["성별"] == "여자"].copy(),
    }
    data["age_total_only"] = data["age_total"][data["age_total"]["연령군"] != "계"].copy()
    data["age_male_only"] = data["age_male"][data["age_male"]["연령군"] != "계"].copy()
    data["age_female_only"] = data["age_female"][data["age_female"]["연령군"] != "계"].copy()
    return data

def savefig(outdir: str, name: str):
    plt.tight_layout()
    path = os.path.join(outdir, name)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()
    print("saved:", path)

def draw_policy_line():
    plt.axvline(POLICY_YEAR, linestyle="--", linewidth=1.5)

def make_index(df: pd.DataFrame, year_col: str, value_col: str, base_year: int) -> pd.DataFrame:
    tmp = df.copy()
    base = tmp.loc[tmp[year_col] == base_year, value_col].iloc[0]
    tmp[f"index_{base_year}=100"] = tmp[value_col] / base * 100
    return tmp

def age_change_table(df: pd.DataFrame, sex_label: str) -> pd.DataFrame:
    pivot = df.pivot_table(index="연령군", columns="연도", values="조발생률", aggfunc="first")
    out = pd.DataFrame(index=pivot.index)
    out["2012"] = pivot.get(2012)
    out["2015"] = pivot.get(2015)
    out["2023"] = pivot.get(2023)
    out["2012→2015 변화율(%)"] = (out["2015"] - out["2012"]) / out["2012"] * 100
    out["2015→2023 변화율(%)"] = (out["2023"] - out["2015"]) / out["2015"] * 100
    out["성별"] = sex_label
    return out.reset_index()

def weighted_mean_age(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df[df["연령군"] != "계"].copy()
    tmp = tmp.dropna(subset=["연령중앙값", "발생자수"])
    out = tmp.groupby("연도").apply(
        lambda x: np.average(x["연령중앙값"], weights=x["발생자수"])
    ).reset_index(name="가중평균연령")
    return out

def fit_its(df: pd.DataFrame, year_col: str, value_col: str, policy_year: int = POLICY_YEAR):
    d = df[[year_col, value_col]].dropna().copy().sort_values(year_col)
    d["time"] = d[year_col] - d[year_col].min()
    d["post"] = (d[year_col] >= policy_year).astype(int)
    d["time_after_policy"] = (d[year_col] - policy_year).clip(lower=0)

    X = sm.add_constant(d[["time", "post", "time_after_policy"]], has_constant="add")
    y = d[value_col]
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    d["fitted"] = model.predict(X)

    pre = d[d[year_col] < policy_year].copy()
    if len(pre) >= 3:
        X_pre = sm.add_constant(pre[["time"]], has_constant="add")
        pre_model = sm.OLS(pre[value_col], X_pre).fit()
        X_cf = sm.add_constant(d[["time"]], has_constant="add")
        d["counterfactual"] = pre_model.predict(X_cf)
        d.loc[d[year_col] < policy_year, "counterfactual"] = np.nan
    else:
        d["counterfactual"] = np.nan

    coef = pd.DataFrame({
        "term": model.params.index,
        "coef": model.params.values,
        "pvalue": model.pvalues.values,
        "ci_low": model.conf_int()[0].values,
        "ci_high": model.conf_int()[1].values
    })
    return model, d, coef

def run_analysis(
    main_source: str,
    age_source: str,
    outdir: str = "thyroid_analysis_outputs",
):
    os.makedirs(outdir, exist_ok=True)
    setup_korean_font()

    main_df = load_main_incidence(main_source)
    age_df = load_age_sex_incidence(age_source)
    parts = prepare_subsets(main_df, age_df)

    main_df.to_csv(f"{outdir}/thyroid_incidence_main.csv", index=False, encoding="utf-8-sig")
    age_df.to_csv(f"{outdir}/thyroid_age_sex_long.csv", index=False, encoding="utf-8-sig")

    overall = parts["overall"]
    male = parts["male"]
    female = parts["female"]
    age_total_only = parts["age_total_only"]
    age_male_only = parts["age_male_only"]
    age_female_only = parts["age_female_only"]
    age_total = parts["age_total"]
    age_male = parts["age_male"]
    age_female = parts["age_female"]

    def get_asr(df, year):
        s = df.loc[df["발생연도"] == year, "연령표준화발생률"]
        return s.iloc[0] if len(s) else np.nan

    summary_change = []
    for label, d in [("전체", overall), ("남자", male), ("여자", female)]:
        y2012 = get_asr(d, 2012)
        y2015 = get_asr(d, 2015)
        y2023 = get_asr(d, 2023)
        summary_change.append({
            "집단": label,
            "2012_ASR": y2012,
            "2015_ASR": y2015,
            "2023_ASR": y2023,
            "2012→2015 변화율(%)": pct_change(y2012, y2015),
            "2015→2023 변화율(%)": pct_change(y2015, y2023),
            "2012→2023 변화율(%)": pct_change(y2012, y2023),
        })
    summary_change = pd.DataFrame(summary_change)
    summary_change.to_csv(f"{outdir}/summary_change_overall_sex.csv", index=False, encoding="utf-8-sig")

    age_change_total = age_change_table(age_total_only, "계")
    age_change_male = age_change_table(age_male_only, "남자")
    age_change_female = age_change_table(age_female_only, "여자")
    age_change_all = pd.concat([age_change_total, age_change_male, age_change_female], ignore_index=True)
    age_change_all.to_csv(f"{outdir}/age_change_all.csv", index=False, encoding="utf-8-sig")

    # Figure 1
    plt.figure(figsize=(10, 5))
    plt.plot(overall["발생연도"], overall["연령표준화발생률"], marker="o", linewidth=2.5)
    draw_policy_line()
    plt.title("갑상선암 연령표준화발생률 추세 (전체)")
    plt.xlabel("연도")
    plt.ylabel("연령표준화발생률")
    savefig(outdir, "figure01_overall_asr_trend.png")

    # Figure 2
    plt.figure(figsize=(10, 5))
    plt.plot(male["발생연도"], male["연령표준화발생률"], marker="o", linewidth=2, label="남자")
    plt.plot(female["발생연도"], female["연령표준화발생률"], marker="o", linewidth=2, label="여자")
    draw_policy_line()
    plt.title("갑상선암 연령표준화발생률 추세 (남녀 비교)")
    plt.xlabel("연도")
    plt.ylabel("연령표준화발생률")
    plt.legend()
    savefig(outdir, "figure02_sex_asr_trend.png")

    # Figure 3
    overall_idx = make_index(overall, "발생연도", "연령표준화발생률", PEAK_YEAR)
    male_idx = make_index(male, "발생연도", "연령표준화발생률", PEAK_YEAR)
    female_idx = make_index(female, "발생연도", "연령표준화발생률", PEAK_YEAR)
    female_mid = age_female_only[age_female_only["연령군"].isin(["50-54세", "55-59세"])].copy()
    female_mid = female_mid.groupby("연도", as_index=False)["조발생률"].mean()
    base_mid = female_mid.loc[female_mid["연도"] == PEAK_YEAR, "조발생률"].iloc[0]
    female_mid[f"index_{PEAK_YEAR}=100"] = female_mid["조발생률"] / base_mid * 100

    plt.figure(figsize=(10, 5))
    plt.plot(overall_idx["발생연도"], overall_idx[f"index_{PEAK_YEAR}=100"], marker="o", linewidth=2, label="전체")
    plt.plot(male_idx["발생연도"], male_idx[f"index_{PEAK_YEAR}=100"], marker="o", linewidth=2, label="남자")
    plt.plot(female_idx["발생연도"], female_idx[f"index_{PEAK_YEAR}=100"], marker="o", linewidth=2, label="여자")
    plt.plot(female_mid["연도"], female_mid[f"index_{PEAK_YEAR}=100"], marker="o", linewidth=2, label="여성 50–59세(평균)")
    draw_policy_line()
    plt.title(f"갑상선암 발생 충격지수 ({PEAK_YEAR}=100)")
    plt.xlabel("연도")
    plt.ylabel("지수")
    plt.legend()
    savefig(outdir, "figure03_shock_index_2012_100.png")

    # Figure 4
    sex_ratio = overall[["발생연도"]].copy()
    sex_ratio["여자_ASR"] = female["연령표준화발생률"].values
    sex_ratio["남자_ASR"] = male["연령표준화발생률"].values
    sex_ratio["여성/남성 비율"] = sex_ratio["여자_ASR"] / sex_ratio["남자_ASR"]
    sex_ratio.to_csv(f"{outdir}/sex_ratio_timeseries.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(10, 5))
    plt.plot(sex_ratio["발생연도"], sex_ratio["여성/남성 비율"], marker="o", linewidth=2.2)
    draw_policy_line()
    plt.title("갑상선암 여성/남성 발생률 비율 추세")
    plt.xlabel("연도")
    plt.ylabel("여성/남성 비율")
    savefig(outdir, "figure04_female_male_ratio.png")

    # Figure 5
    plot_df = age_total_only[age_total_only["연도"].isin(COMPARE_YEARS)].copy()
    plt.figure(figsize=(10, 5))
    for yr in COMPARE_YEARS:
        g = plot_df[plot_df["연도"] == yr].copy()
        plt.plot(g["연령군"], g["조발생률"], marker="o", linewidth=2, label=str(yr))
    plt.xticks(rotation=45)
    plt.title("갑상선암 연령군별 조발생률 프로파일 (전체)")
    plt.xlabel("연령군")
    plt.ylabel("조발생률")
    plt.legend()
    savefig(outdir, "figure05_age_profile_total_2012_2015_2023.png")

    # Figure 6 butterfly
    years = [2012, 2015, 2023]
    fig, axes = plt.subplots(1, 3, figsize=(16, 8), sharey=True)
    for ax, yr in zip(axes, years):
        m = age_male_only[age_male_only["연도"] == yr].copy().sort_values("연령중앙값")
        f = age_female_only[age_female_only["연도"] == yr].copy().sort_values("연령중앙값")
        y = np.arange(len(m))
        labels = m["연령군"].tolist()
        ax.barh(y, -m["조발생률"].values, alpha=0.8, label="남자")
        ax.barh(y, f["조발생률"].values, alpha=0.8, label="여자")
        ax.axvline(0, linewidth=1)
        ax.set_title(f"{yr}")
        ax.set_yticks(y)
        ax.set_yticklabels(labels)
        ax.set_xlabel("조발생률")
    axes[0].legend(loc="lower right")
    fig.suptitle("갑상선암 발생의 성별·연령 구조 변화 (버터플라이 비교)")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f"{outdir}/figure06_butterfly_2012_2015_2023.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Figure 7 Heatmap
    order = age_total_only[["연령군", "연령중앙값"]].drop_duplicates().sort_values("연령중앙값")["연령군"]
    heat = age_total_only.pivot(index="연령군", columns="연도", values="조발생률").loc[order]
    plt.figure(figsize=(12, 7))
    plt.imshow(heat.values, aspect="auto")
    plt.colorbar(label="조발생률")
    plt.xticks(np.arange(len(heat.columns)), heat.columns, rotation=90)
    plt.yticks(np.arange(len(heat.index)), heat.index)
    plt.title("갑상선암 연령군별 조발생률 Heatmap (전체)")
    plt.xlabel("연도")
    plt.ylabel("연령군")
    savefig(outdir, "figure07_heatmap_total.png")

    # Figure 8 Heatmap female
    heat_f = age_female_only.pivot(index="연령군", columns="연도", values="조발생률").loc[order]
    plt.figure(figsize=(12, 7))
    plt.imshow(heat_f.values, aspect="auto")
    plt.colorbar(label="조발생률")
    plt.xticks(np.arange(len(heat_f.columns)), heat_f.columns, rotation=90)
    plt.yticks(np.arange(len(heat_f.index)), heat_f.index)
    plt.title("갑상선암 연령군별 조발생률 Heatmap (여성)")
    plt.xlabel("연도")
    plt.ylabel("연령군")
    savefig(outdir, "figure08_heatmap_female.png")

    # Figure 9
    wf1 = age_change_total.copy().sort_values("2012→2015 변화율(%)")
    plt.figure(figsize=(11, 6))
    plt.bar(wf1["연령군"], wf1["2012→2015 변화율(%)"])
    plt.xticks(rotation=45)
    plt.title("연령군별 감소율: 2012 → 2015 (전체)")
    plt.xlabel("연령군")
    plt.ylabel("변화율 (%)")
    savefig(outdir, "figure09_waterfall_drop_total_2012_2015.png")

    # Figure 10
    wf2 = age_change_total.copy().sort_values("2015→2023 변화율(%)", ascending=False)
    plt.figure(figsize=(11, 6))
    plt.bar(wf2["연령군"], wf2["2015→2023 변화율(%)"])
    plt.xticks(rotation=45)
    plt.title("연령군별 rebound: 2015 → 2023 (전체)")
    plt.xlabel("연령군")
    plt.ylabel("변화율 (%)")
    savefig(outdir, "figure10_waterfall_rebound_total_2015_2023.png")

    # Figure 11
    wf3 = age_change_female.copy().sort_values("2012→2015 변화율(%)")
    plt.figure(figsize=(11, 6))
    plt.bar(wf3["연령군"], wf3["2012→2015 변화율(%)"])
    plt.xticks(rotation=45)
    plt.title("연령군별 감소율: 2012 → 2015 (여성)")
    plt.xlabel("연령군")
    plt.ylabel("변화율 (%)")
    savefig(outdir, "figure11_waterfall_drop_female_2012_2015.png")

    # Figure 12
    bubble = age_df[(age_df["연도"] == 2023) & (age_df["연령군"] != "계")].copy()
    bubble["x"] = bubble["연령중앙값"]
    bubble["size"] = bubble["발생자수"] / bubble["발생자수"].max() * 1800
    plt.figure(figsize=(11, 6))
    for sex in ["남자", "여자"]:
        g = bubble[bubble["성별"] == sex].copy()
        plt.scatter(g["x"], g["조발생률"], s=g["size"], alpha=0.6, label=sex)
    xtick_positions = sorted(bubble["연령중앙값"].dropna().unique())
    xtick_labels = bubble.dropna(subset=["연령중앙값"]).drop_duplicates("연령중앙값").sort_values("연령중앙값")["연령군"]
    plt.xticks(xtick_positions, xtick_labels, rotation=45)
    plt.title("갑상선암 성별·연령별 burden (2023)")
    plt.xlabel("연령군")
    plt.ylabel("조발생률")
    plt.legend()
    savefig(outdir, "figure12_bubble_2023.png")

    # Figure 13
    mean_age_total = weighted_mean_age(age_total)
    mean_age_male = weighted_mean_age(age_male)
    mean_age_female = weighted_mean_age(age_female)
    plt.figure(figsize=(10, 5))
    plt.plot(mean_age_total["연도"], mean_age_total["가중평균연령"], marker="o", linewidth=2, label="전체")
    plt.plot(mean_age_male["연도"], mean_age_male["가중평균연령"], marker="o", linewidth=2, label="남자")
    plt.plot(mean_age_female["연도"], mean_age_female["가중평균연령"], marker="o", linewidth=2, label="여자")
    draw_policy_line()
    plt.title("갑상선암 발생의 가중평균연령 추세 (근사치)")
    plt.xlabel("연도")
    plt.ylabel("연령(세)")
    plt.legend()
    savefig(outdir, "figure13_weighted_mean_age.png")

    mean_age_all = mean_age_total.merge(mean_age_male, on="연도", suffixes=("_전체", "_남자"))
    mean_age_all = mean_age_all.merge(mean_age_female, on="연도")
    mean_age_all = mean_age_all.rename(columns={"가중평균연령": "가중평균연령_여자"})
    mean_age_all.to_csv(f"{outdir}/weighted_mean_age.csv", index=False, encoding="utf-8-sig")

    # Figure 14
    sel_ages = ["20-24세", "30-34세", "40-44세", "50-54세", "60-64세"]
    ratio_rows = []
    for ag in sel_ages:
        m = age_male_only[age_male_only["연령군"] == ag][["연도", "조발생률"]].rename(columns={"조발생률": "남자"})
        f = age_female_only[age_female_only["연령군"] == ag][["연도", "조발생률"]].rename(columns={"조발생률": "여자"})
        r = pd.merge(m, f, on="연도", how="inner")
        r["연령군"] = ag
        r["여성/남성 비율"] = r["여자"] / r["남자"]
        ratio_rows.append(r)
    ratio_age = pd.concat(ratio_rows, ignore_index=True)
    ratio_age.to_csv(f"{outdir}/ratio_by_agegroup.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(11, 6))
    for ag in sel_ages:
        g = ratio_age[ratio_age["연령군"] == ag]
        plt.plot(g["연도"], g["여성/남성 비율"], marker="o", linewidth=2, label=ag)
    draw_policy_line()
    plt.title("연령군별 여성/남성 비율 추세")
    plt.xlabel("연도")
    plt.ylabel("여성/남성 비율")
    plt.legend(ncol=2)
    savefig(outdir, "figure14_ratio_by_agegroup.png")

    # ITS
    its_results = {}
    for label, df_ in [("전체", overall), ("남자", male), ("여자", female)]:
        model, fit_df, coef = fit_its(df_, "발생연도", "연령표준화발생률", policy_year=POLICY_YEAR)
        its_results[label] = {"model": model, "fit_df": fit_df, "coef": coef}
        coef.to_csv(f"{outdir}/its_coef_{label}.csv", index=False, encoding="utf-8-sig")
        fit_df.to_csv(f"{outdir}/its_fit_{label}.csv", index=False, encoding="utf-8-sig")

        plt.figure(figsize=(10, 5))
        plt.plot(fit_df["발생연도"], fit_df["연령표준화발생률"], marker="o", linewidth=2, label="관측값")
        plt.plot(fit_df["발생연도"], fit_df["fitted"], linewidth=2, label="ITS 적합선")
        plt.plot(fit_df["발생연도"], fit_df["counterfactual"], linestyle="--", linewidth=2, label="반사실")
        draw_policy_line()
        plt.title(f"ITS: 갑상선암 연령표준화발생률 ({label})")
        plt.xlabel("연도")
        plt.ylabel("연령표준화발생률")
        plt.legend()
        savefig(outdir, f"figure_its_{label}.png")

    # Summary text
    def get_asr_value(df, year):
        s = df.loc[df["발생연도"] == year, "연령표준화발생률"]
        return s.iloc[0] if len(s) else np.nan

    y1999 = get_asr_value(overall, 1999)
    y2012 = get_asr_value(overall, 2012)
    y2015 = get_asr_value(overall, 2015)
    y2023 = get_asr_value(overall, 2023)

    lines = [
        "===== 자동 해석 =====",
        f"1) 전체 연령표준화발생률은 1999년 {y1999:.1f}에서 2012년 {y2012:.1f}로 증가했다.",
        f"2) 이후 2015년 {y2015:.1f}로 감소하여, 2012년 대비 {pct_change(y2012, y2015):.1f}% 변화하였다.",
        f"3) 2023년 {y2023:.1f}로 일부 재상승했으나, 2012년 정점에는 미치지 못했다.",
        "",
        "4) 2012→2015 감소폭 상위 연령군",
        age_change_total.sort_values("2012→2015 변화율(%)").head(5).to_string(index=False),
        "",
        "5) 2015→2023 rebound 상위 연령군",
        age_change_total.sort_values("2015→2023 변화율(%)", ascending=False).head(5).to_string(index=False),
    ]

    for label in ["전체", "남자", "여자"]:
        coef = its_results[label]["coef"].copy()
        post = coef.loc[coef["term"] == "post", "coef"].iloc[0]
        post_p = coef.loc[coef["term"] == "post", "pvalue"].iloc[0]
        slope = coef.loc[coef["term"] == "time_after_policy", "coef"].iloc[0]
        slope_p = coef.loc[coef["term"] == "time_after_policy", "pvalue"].iloc[0]
        lines += [
            "",
            f"[{label}]",
            f"- 정책 직후 수준 변화(post): {post:.3f} (p={post_p:.4f})",
            f"- 정책 후 추세 변화(time_after_policy): {slope:.3f} (p={slope_p:.4f})",
        ]

    with open(f"{outdir}/auto_summary.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {
        "main_df": main_df,
        "age_df": age_df,
        "summary_change": summary_change,
        "age_change_total": age_change_total,
        "age_change_female": age_change_female,
        "outdir": outdir,
    }
