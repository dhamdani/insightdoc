"""Analisis penjualan (FR-8). Semua angka deterministik dari data."""
from __future__ import annotations

import pandas as pd

from .cleaning import coerce_date, coerce_numeric


def analyze_sales(df: pd.DataFrame, mapping: dict) -> dict:
    out: dict = {"sections": []}
    date_col, amt_col = mapping.get("date_col"), mapping.get("amount_col")
    grp_col, qty_col = mapping.get("group_col"), mapping.get("qty_col")

    if not amt_col or amt_col not in df.columns:
        nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        amt_col = amt_col or (nums[0] if nums else None)
    if not amt_col:
        out["error"] = "Tidak ada kolom numerik untuk analisis penjualan."
        return out

    work = df.copy()
    work["_amount"] = coerce_numeric(work[amt_col])
    work = work.dropna(subset=["_amount"])
    total = float(work["_amount"].sum())
    out["total"] = total
    out["n_rows"] = len(work)
    out["avg_per_row"] = float(work["_amount"].mean()) if len(work) else 0.0

    # Tren per periode
    trend = []
    period_label = None
    if date_col and date_col in df.columns:
        work["_date"] = coerce_date(work[date_col])
        wd = work.dropna(subset=["_date"])
        if len(wd) >= 2:
            span_days = (wd["_date"].max() - wd["_date"].min()).days
            freq = "ME" if span_days > 62 else "W" if span_days > 14 else "D"
            period_label = {"ME": "bulan", "W": "minggu", "D": "hari"}[freq]
            g = wd.groupby(pd.Grouper(key="_date", freq=freq))["_amount"].sum()
            trend = [{"periode": d.strftime("%Y-%m-%d"), "nilai": float(v)} for d, v in g.items()]
            out["period_label"] = period_label
            out["trend"] = trend
            if len(g) >= 2:
                last, prev = float(g.iloc[-1]), float(g.iloc[-2])
                out["mom_growth_pct"] = round((last - prev) / abs(prev) * 100, 1) if prev != 0 else None
    out["trend"] = trend

    # Top/bottom performer
    if grp_col and grp_col in df.columns:
        g = work.groupby(grp_col)["_amount"].sum().sort_values(ascending=False)
        out["top_groups"] = [{"nama": str(i), "nilai": float(v), "share_pct": round(float(v) / total * 100, 1) if total else 0} for i, v in g.head(5).items()]
        out["bottom_groups"] = [{"nama": str(i), "nilai": float(v)} for i, v in g.tail(3).items()]
    else:
        out["top_groups"] = []
        out["bottom_groups"] = []

    # Outlier: > mean + 2*std
    if len(work) >= 5:
        mu, sd = work["_amount"].mean(), work["_amount"].std()
        outl = work[work["_amount"] > mu + 2 * sd].sort_values("_amount", ascending=False).head(5)
        out["outliers"] = [{"index": int(i), "nilai": float(r["_amount"])} for i, r in outl.iterrows()]
        out["mean"], out["std"] = float(mu), float(sd or 0)
    else:
        out["outliers"] = []

    # Temuan naratif
    findings = []
    findings.append(f"Total nilai {amt_col} tercatat {total:,.0f} dari {len(work)} baris data.")
    if out.get("mom_growth_pct") is not None:
        d = out["mom_growth_pct"]
        arah = "naik" if d >= 0 else "turun"
        findings.append(f"Periode terakhir {arah} {abs(d)}% dibanding periode sebelumnya.")
    if out["top_groups"]:
        t0 = out["top_groups"][0]
        findings.append(f"Kontributor terbesar: {t0['nama']} ({t0['share_pct']}% dari total).")
    if out.get("bottom_groups"):
        b0 = out["bottom_groups"][0]
        findings.append(f"Performa terlemah: {b0['nama']} (nilai {b0['nilai']:,.0f}).")
    if out.get("outliers"):
        findings.append(f"Terdeteksi {len(out['outliers'])} anomali penjualan di atas ambang normal (mean+2σ).")
    out["findings"] = findings
    return out
