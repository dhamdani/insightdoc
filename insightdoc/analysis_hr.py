"""Analisis karyawan/HR (FR-9)."""
from __future__ import annotations

import pandas as pd

from .cleaning import coerce_date, coerce_numeric


def _find_col(df: pd.DataFrame, hints: list[str]) -> str | None:
    low = {c: str(c).lower() for c in df.columns}
    for c in df.columns:
        if any(h in low[c] for h in hints):
            return c
    return None


def analyze_hr(df: pd.DataFrame, mapping: dict) -> dict:
    out: dict = {}
    dept_col = mapping.get("group_col") or _find_col(df, ["departemen", "department", "divisi", "division", "bagian"])
    salary_col = mapping.get("amount_col") or _find_col(df, ["gaji", "salary", "upah", "kompensasi"])
    status_col = _find_col(df, ["status", "keluar", "aktif", "resign", "turnover"])
    join_col = mapping.get("date_col") or _find_col(df, ["masuk", "join", "gabung", "mulai"])

    out["headcount"] = len(df)
    findings = [f"Total headcount tercatat: {len(df)} karyawan."]

    if dept_col and dept_col in df.columns:
        dist = df[dept_col].value_counts()
        out["dept_dist"] = [{"nama": str(i), "jumlah": int(v)} for i, v in dist.items()]
        findings.append(f"Departemen terbesar: {dist.index[0]} ({int(dist.iloc[0])} orang).")
    else:
        out["dept_dist"] = []

    if salary_col and salary_col in df.columns:
        s = coerce_numeric(df[salary_col]).dropna()
        if len(s):
            out["salary"] = {"mean": float(s.mean()), "median": float(s.median()), "min": float(s.min()), "max": float(s.max()), "std": float(s.std() or 0)}
            ratio = float(s.max() / s.mean()) if s.mean() else 0
            out["salary"]["max_to_mean_ratio"] = round(ratio, 2)
            findings.append(f"Rata-rata gaji {s.mean():,.0f}, median {s.median():,.0f} (min {s.min():,.0f} – maks {s.max():,.0f}).")
            if ratio > 3:
                findings.append("Indikasi ketimpangan kompensasi: gaji maksimum >3x rata-rata — perlu tinjauan struktur penggajian.")
            if dept_col and dept_col in df.columns:
                per_dept = df.assign(_s=coerce_numeric(df[salary_col])).groupby(dept_col)["_s"].mean().sort_values(ascending=False)
                out["salary_per_dept"] = [{"nama": str(i), "rata2": float(v)} for i, v in per_dept.items()]
        else:
            out["salary"] = {}
    else:
        out["salary"] = {}

    if status_col and status_col in df.columns:
        vals = df[status_col].astype(str).str.lower()
        out_vals = vals[vals.str.contains("keluar|resign|nonaktif|non-aktif|tidak aktif|exit|termin")]
        rate = len(out_vals) / len(df) * 100 if len(df) else 0
        out["turnover_rate_pct"] = round(rate, 1)
        findings.append(f"Turnover tercatat {rate:.1f}% dari headcount pada dataset ini.")
    else:
        out["turnover_rate_pct"] = None

    if join_col and join_col in df.columns:
        d = coerce_date(df[join_col]).dropna()
        if len(d):
            out["join_range"] = {"min": str(d.min().date()), "max": str(d.max().date())}
            tenure_years = ((pd.Timestamp.now() - d).dt.days / 365.25)
            out["tenure"] = {"mean_years": round(float(tenure_years.mean()), 1), "median_years": round(float(tenure_years.median()), 1)}
            findings.append(f"Rata-rata masa kerja {out['tenure']['mean_years']} tahun (median {out['tenure']['median_years']} tahun).")
    out["findings"] = findings
    return out
