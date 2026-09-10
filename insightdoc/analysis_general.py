"""Analisis umum/generik (FR-11): statistik deskriptif + korelasi sederhana."""
from __future__ import annotations

import pandas as pd


def analyze_general(df: pd.DataFrame, mapping: dict) -> dict:
    out: dict = {}
    nums = df.select_dtypes(include="number").columns.tolist()
    # Coba koersi kolom objek yang tampak numerik
    for c in df.columns:
        if c not in nums:
            s = pd.to_numeric(df[c].astype(str).str.replace(r"[^\d.,\-]", "", regex=True).str.replace(",", "", regex=False), errors="coerce")
            if s.notna().mean() > 0.7:
                nums.append(c)
    desc = {}
    for c in nums[:10]:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s):
            desc[c] = {"mean": float(s.mean()), "median": float(s.median()), "min": float(s.min()), "max": float(s.max()), "std": float(s.std() or 0), "n": int(s.count())}
    out["descriptives"] = desc
    if len(nums) >= 2:
        try:
            corr = df[nums[:8]].apply(pd.to_numeric, errors="coerce").corr(numeric_only=True)
            pairs = []
            for i in range(len(corr.columns)):
                for j in range(i + 1, len(corr.columns)):
                    v = corr.iloc[i, j]
                    if pd.notna(v) and abs(float(v)) >= 0.5:
                        pairs.append({"a": corr.columns[i], "b": corr.columns[j], "corr": round(float(v), 2)})
            out["strong_correlations"] = sorted(pairs, key=lambda x: -abs(x["corr"]))[:5]
        except Exception:
            out["strong_correlations"] = []
    else:
        out["strong_correlations"] = []
    findings = [f"Kolom numerik terdeteksi: {len(nums)}."] if nums else ["Tidak ada kolom numerik yang jelas."]
    for c, d in list(desc.items())[:3]:
        findings.append(f"{c}: rata-rata {d['mean']:,.2f}, median {d['median']:,.2f}.")
    for p in out["strong_correlations"][:3]:
        findings.append(f"Korelasi kuat {p['a']} ↔ {p['b']} (r={p['corr']}).")
    out["findings"] = findings
    return out
