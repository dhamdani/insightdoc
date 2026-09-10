"""Orkestrasi mesin analisis (PRD §9): parsing → deteksi → analisis → rekomendasi."""
from __future__ import annotations

import pandas as pd

from .analysis_cashflow import analyze_cashflow
from .analysis_general import analyze_general
from .analysis_hr import analyze_hr
from .analysis_sales import analyze_sales
from .cleaning import clean_dataframe, cleaning_report
from .detection import detect_category, suggest_mapping
from .recommendations import build_recommendations


def run_analysis(df: pd.DataFrame, category: str | None = None,
                 mapping: dict | None = None, lang: str = "id") -> dict:
    report = cleaning_report(df)
    cleaned = clean_dataframe(df)
    detected = detect_category(cleaned)
    cat = category or detected["category"]
    mp = mapping or suggest_mapping(cleaned, cat)
    fn = {"penjualan": analyze_sales, "karyawan": analyze_hr,
          "cashflow": analyze_cashflow, "umum": analyze_general}.get(cat, analyze_general)
    result = fn(cleaned, mp)
    recs = build_recommendations(cat, result, lang)
    summary = build_executive_summary(cat, result, recs, lang)
    return {
        "category": cat,
        "detected": detected,
        "mapping": mp,
        "cleaning": report,
        "result": result,
        "recommendations": recs,
        "executive_summary": summary,
        "n_rows": len(cleaned),
        "lang": lang,
    }


def build_executive_summary(cat: str, result: dict, recs: list[dict], lang: str) -> str:
    findings = result.get("findings", [])
    n_high = sum(1 for r in recs if r["prioritas"] == "Tinggi")
    if lang == "en":
        s = f"Analysis of {len(findings)} key findings in category '{cat}'. "
        s += " ".join(findings[:3])
        s += f" {len(recs)} actions recommended ({n_high} high priority)." if recs else ""
    else:
        s = f"Analisis menemukan {len(findings)} temuan utama pada kategori '{cat}'. "
        s += " ".join(findings[:3])
        s += f" Dihasilkan {len(recs)} rekomendasi tindakan ({n_high} prioritas tinggi)." if recs else ""
    return s
