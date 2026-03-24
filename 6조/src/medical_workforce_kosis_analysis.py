import io
import os
import re
import json
import math
import shutil
import zipfile
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import quote

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import pearsonr
import statsmodels.formula.api as smf


@dataclass
class RepoConfig:
    github_user: str = "runmc3812"
    repo_name: str = "Healthcare_Informatics_Integration-2026-"
    branch: str = "main"
    base_path: str = "1조/medical_workforce_kosis"

    age_file: str = "고령인구비율_시도_시_군_구__20260324171859.csv"
    migration_file: str = "순이동인구_시도_시_군_구__20260324172019.csv"
    population_file: str = "주민등록인구_시도_시_군_구__20260324172055.csv"
    doctor_file: str = "인구_천명당_의료기관_종사_의사수_시도_시_군_구__20260324172132.csv"

    data_dir: str = "data"
    output_dir: str = "outputs"

    def raw_url(self, *parts: str) -> str:
        encoded = "/".join(quote(str(p)) for p in parts)
        return f"https://raw.githubusercontent.com/{self.github_user}/{self.repo_name}/{self.branch}/{encoded}"


REGION_ORDER = [
    "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시",
    "울산광역시", "세종특별자치시", "경기도", "강원특별자치도", "충청북도", "충청남도",
    "전북특별자치도", "전라남도", "경상북도", "경상남도", "제주특별자치도",
]
CAPITAL_REGIONS = {"서울특별시", "인천광역시", "경기도"}


def _try_read_csv(raw: bytes) -> pd.DataFrame:
    last = None
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except Exception as e:
            last = e
    raise last


def read_csv_any(source: str) -> pd.DataFrame:
    if re.match(r"https?://", source):
        import requests
        resp = requests.get(source, timeout=60)
        resp.raise_for_status()
        return _try_read_csv(resp.content)
    with open(source, "rb") as f:
        return _try_read_csv(f.read())


def pick_local_or_url(cfg: RepoConfig, filename: str) -> str:
    local = os.path.join(cfg.data_dir, filename)
    if os.path.exists(local):
        return local
    return cfg.raw_url(cfg.base_path, cfg.data_dir, filename)


def clean_num(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().replace(",", "")
    if s in {"", "-", "…", "nan"}:
        return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def _filter_regions(df: pd.DataFrame, region_col: str) -> pd.DataFrame:
    out = df.copy()
    out = out[out[region_col].isin(REGION_ORDER)].copy()
    out[region_col] = pd.Categorical(out[region_col], categories=REGION_ORDER, ordered=True)
    out = out.sort_values(region_col).copy()
    out[region_col] = out[region_col].astype(str)
    return out


def parse_triplet_wide(df: pd.DataFrame, region_col: str, kind: str) -> pd.DataFrame:
    # first row is metric row in these KOSIS files
    body = df.iloc[1:].copy().reset_index(drop=True)
    body = _filter_regions(body, region_col)

    years = sorted({re.sub(r"\.\d+$", "", c) for c in body.columns if re.match(r"^\d{4}(?:\.\d+)?$", str(c))})
    records = []
    for _, row in body.iterrows():
        region = row[region_col]
        for y in years:
            cols = [c for c in body.columns if re.sub(r"\.\d+$", "", str(c)) == y]
            cols = sorted(cols, key=lambda x: (0 if str(x) == y else int(str(x).split(".")[1])))
            vals = [clean_num(row[c]) for c in cols]
            rec = {"year": int(y), "region": region}
            if kind == "age":
                rec.update({"aged_ratio": vals[0], "age65_pop": vals[1], "age_total_pop_from_agefile": vals[2]})
            elif kind == "population":
                rec.update({"population": vals[0], "male_population": vals[1], "female_population": vals[2]})
            elif kind == "doctor":
                rec.update({"physician_per_1000": vals[0], "physician_count": vals[1], "population_from_doctorfile": vals[2]})
            records.append(rec)
    return pd.DataFrame(records)


def parse_migration_wide(df: pd.DataFrame) -> pd.DataFrame:
    body = df.copy()
    body = body[body["성별(1)"].astype(str) == "계"].copy()
    body = _filter_regions(body, "행정구역(시군구)별(1)")
    years = [c for c in body.columns if re.match(r"^\d{4}$", str(c))]
    records = []
    for _, row in body.iterrows():
        region = row["행정구역(시군구)별(1)"]
        for y in years:
            records.append({
                "year": int(y),
                "region": region,
                "net_migration": clean_num(row[y]),
            })
    return pd.DataFrame(records)


def build_panel(cfg: RepoConfig) -> pd.DataFrame:
    age_raw = read_csv_any(pick_local_or_url(cfg, cfg.age_file))
    mig_raw = read_csv_any(pick_local_or_url(cfg, cfg.migration_file))
    pop_raw = read_csv_any(pick_local_or_url(cfg, cfg.population_file))
    doc_raw = read_csv_any(pick_local_or_url(cfg, cfg.doctor_file))

    age = parse_triplet_wide(age_raw, "행정구역별(1)", "age")
    mig = parse_migration_wide(mig_raw)
    pop = parse_triplet_wide(pop_raw, "행정구역별", "population")
    doc = parse_triplet_wide(doc_raw, "행정구역별", "doctor")

    panel = age.merge(mig, on=["year", "region"], how="inner")
    panel = panel.merge(pop, on=["year", "region"], how="inner")
    panel = panel.merge(doc, on=["year", "region"], how="inner")

    panel = panel[(panel["year"] >= 2007) & (panel["year"] <= 2024)].copy()
    panel["capital_region"] = panel["region"].isin(CAPITAL_REGIONS).astype(int)
    panel["capital_label"] = panel["capital_region"].map({1: "수도권", 0: "비수도권"})
    panel["net_migration_rate"] = panel["net_migration"] / panel["population"] * 10000
    panel["log_population"] = np.log(panel["population"])

    panel["doctor_rank"] = panel.groupby("year")["physician_per_1000"].rank(ascending=False, method="min")
    panel["aged_rank"] = panel.groupby("year")["aged_ratio"].rank(ascending=False, method="min")

    panel["region"] = pd.Categorical(panel["region"], categories=REGION_ORDER, ordered=True)
    panel = panel.sort_values(["year", "region"]).reset_index(drop=True)
    panel["region"] = panel["region"].astype(str)
    return panel


def save_fig(fig, outdir: str, stem: str):
    html_path = os.path.join(outdir, f"{stem}.html")
    fig.write_html(html_path)
    try:
        fig.write_image(os.path.join(outdir, f"{stem}.png"), scale=2)
    except Exception:
        pass


def make_figures(panel: pd.DataFrame, outdir: str):
    # 1. national mean indexed trend
    trend = panel.groupby("year", as_index=False)[["aged_ratio", "net_migration_rate", "physician_per_1000"]].mean()
    for col in ["aged_ratio", "net_migration_rate", "physician_per_1000"]:
        base = trend.iloc[0][col]
        trend[f"{col}_idx"] = trend[col] / base * 100
    long = trend.melt(id_vars="year", value_vars=["aged_ratio_idx", "net_migration_rate_idx", "physician_per_1000_idx"], var_name="indicator", value_name="index")
    label_map = {
        "aged_ratio_idx": "고령인구비율 지수", "net_migration_rate_idx": "순이동률 지수", "physician_per_1000_idx": "의사밀도 지수"
    }
    long["indicator"] = long["indicator"].map(label_map)
    fig = px.line(long, x="year", y="index", color="indicator", markers=True, title="전국 평균 지수 추세 (2007=100)")
    save_fig(fig, outdir, "01_index_trend")

    # 2. region small multiples
    fig = px.line(panel, x="year", y="physician_per_1000", facet_col="region", facet_col_wrap=4, height=950, title="시도별 인구 천명당 의사수 추세")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    save_fig(fig, outdir, "02_region_small_multiples")

    # 3. heatmap
    heat = panel.pivot(index="region", columns="year", values="physician_per_1000").loc[REGION_ORDER]
    fig = px.imshow(heat, aspect="auto", color_continuous_scale="Blues", title="시도×연도 의사밀도 히트맵")
    save_fig(fig, outdir, "03_heatmap")

    latest = int(panel["year"].max())
    latest_df = panel[panel["year"] == latest].copy()

    # 4. aged vs doctor scatter
    fig = px.scatter(latest_df, x="aged_ratio", y="physician_per_1000", text="region", color="capital_label", title=f"{latest}년 고령인구비율과 의사밀도")
    fig.update_traces(textposition="top center")
    save_fig(fig, outdir, "04_aged_vs_doctor")

    # 5. migration bubble
    fig = px.scatter(latest_df, x="net_migration_rate", y="physician_per_1000", size="population", color="capital_label", text="region", size_max=55, title=f"{latest}년 순이동률과 의사밀도")
    fig.update_traces(textposition="top center")
    save_fig(fig, outdir, "05_migration_bubble")

    # 6. capital vs non-capital box
    fig = px.box(panel, x="capital_label", y="physician_per_1000", color="capital_label", points="all", title="수도권 vs 비수도권 의사밀도 분포")
    save_fig(fig, outdir, "06_capital_boxplot")

    # 7. slope graph
    start, end = int(panel["year"].min()), int(panel["year"].max())
    d0 = panel[panel["year"] == start][["region", "physician_per_1000"]].rename(columns={"physician_per_1000": "start"})
    d1 = panel[panel["year"] == end][["region", "physician_per_1000"]].rename(columns={"physician_per_1000": "end"})
    slope = d0.merge(d1, on="region")
    fig = go.Figure()
    for _, r in slope.iterrows():
        fig.add_trace(go.Scatter(x=[start, end], y=[r["start"], r["end"]], mode="lines+markers+text", text=[r["region"], r["region"]], textposition="top center", showlegend=False))
    fig.update_layout(title=f"{start}→{end} 의사밀도 변화", xaxis_title="연도", yaxis_title="의사수/천명")
    save_fig(fig, outdir, "07_slopegraph")

    # 8. bump chart
    fig = px.line(panel, x="year", y="doctor_rank", color="region", title="시도별 의사밀도 순위 변화")
    fig.update_yaxes(autorange="reversed")
    save_fig(fig, outdir, "08_bump_chart")

    # 9. quadrant
    x_mean = latest_df["aged_ratio"].mean()
    y_mean = latest_df["physician_per_1000"].mean()
    fig = px.scatter(latest_df, x="aged_ratio", y="physician_per_1000", text="region", color="capital_label", title=f"{latest}년 고령화-의사밀도 사분면")
    fig.add_vline(x=x_mean, line_dash="dash")
    fig.add_hline(y=y_mean, line_dash="dash")
    fig.update_traces(textposition="top center")
    save_fig(fig, outdir, "09_quadrant")

    # 10. delta bar
    slope["pct_change"] = (slope["end"] - slope["start"]) / slope["start"] * 100
    slope = slope.sort_values("pct_change", ascending=False)
    fig = px.bar(slope, x="region", y="pct_change", color="pct_change", title=f"{start}→{end} 의사밀도 변화율(%)")
    save_fig(fig, outdir, "10_delta_bar")

    # 11. correlation heatmap
    corr = panel[["aged_ratio", "net_migration_rate", "population", "physician_per_1000"]].corr().round(3)
    fig = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title="상관행렬 히트맵")
    save_fig(fig, outdir, "11_correlation_heatmap")

    # 12. ranked bars latest
    latest_df = latest_df.sort_values("physician_per_1000", ascending=False)
    fig = px.bar(latest_df, x="region", y="physician_per_1000", color="capital_label", title=f"{latest}년 시도별 의사밀도 순위")
    save_fig(fig, outdir, "12_latest_ranked_bar")

    return slope, corr


def run_models(panel: pd.DataFrame, outdir: str):
    corr_pairs = []
    for x in ["aged_ratio", "net_migration_rate", "population"]:
        r, p = pearsonr(panel[x], panel["physician_per_1000"])
        corr_pairs.append({"x": x, "y": "physician_per_1000", "pearson_r": r, "p_value": p})
    corr_pairs = pd.DataFrame(corr_pairs)

    m1 = smf.ols("physician_per_1000 ~ aged_ratio", data=panel).fit()
    m2 = smf.ols("physician_per_1000 ~ aged_ratio + net_migration_rate + capital_region + log_population", data=panel).fit()

    def tidy_model(m, name):
        ci = m.conf_int()
        return pd.DataFrame({
            "model": name,
            "term": m.params.index,
            "coef": m.params.values,
            "p_value": m.pvalues.values,
            "ci_low": ci[0].values,
            "ci_high": ci[1].values,
            "r_squared": m.rsquared,
            "n_obs": int(m.nobs),
        })

    reg = pd.concat([tidy_model(m1, "Model 1"), tidy_model(m2, "Model 2")], ignore_index=True)

    corr_pairs.to_csv(os.path.join(outdir, "correlation_pairs.csv"), index=False, encoding="utf-8-sig")
    reg.to_csv(os.path.join(outdir, "regression_results.csv"), index=False, encoding="utf-8-sig")

    with open(os.path.join(outdir, "regression_summary.txt"), "w", encoding="utf-8") as f:
        f.write("[Model 1]\n")
        f.write(m1.summary().as_text())
        f.write("\n\n[Model 2]\n")
        f.write(m2.summary().as_text())

    return corr_pairs, reg


def write_outputs(panel: pd.DataFrame, slope: pd.DataFrame, corr: pd.DataFrame, outdir: str):
    panel.to_csv(os.path.join(outdir, "panel_data.csv"), index=False, encoding="utf-8-sig")
    slope.to_csv(os.path.join(outdir, "slope_data.csv"), index=False, encoding="utf-8-sig")
    corr.to_csv(os.path.join(outdir, "correlation_matrix.csv"), index=True, encoding="utf-8-sig")

    summary = {
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "n_rows": int(len(panel)),
        "n_regions": int(panel["region"].nunique()),
        "variables": ["aged_ratio", "net_migration", "population", "physician_per_1000", "capital_region"],
    }
    with open(os.path.join(outdir, "run_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def zip_outputs(outdir: str) -> str:
    zip_base = os.path.abspath(outdir)
    return shutil.make_archive(zip_base, "zip", outdir)


def main(cfg: Optional[RepoConfig] = None):
    cfg = cfg or RepoConfig()
    os.makedirs(cfg.output_dir, exist_ok=True)

    panel = build_panel(cfg)
    slope, corr = make_figures(panel, cfg.output_dir)
    _, _ = run_models(panel, cfg.output_dir)
    write_outputs(panel, slope, corr, cfg.output_dir)
    zip_path = zip_outputs(cfg.output_dir)

    print("분석 완료")
    print(f"- 데이터 행 수: {len(panel)}")
    print(f"- 지역 수: {panel['region'].nunique()}")
    print(f"- 연도 범위: {panel['year'].min()}~{panel['year'].max()}")
    print(f"- 출력 폴더: {os.path.abspath(cfg.output_dir)}")
    print(f"- ZIP 파일: {zip_path}")
    return panel


if __name__ == "__main__":
    main()
