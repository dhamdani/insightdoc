"""Analisis cashflow/keuangan (FR-10)."""
from __future__ import annotations

import pandas as pd

from .cleaning import coerce_date, coerce_numeric


def analyze_cashflow(df: pd.DataFrame, mapping: dict) -> dict:
    out: dict = {}
    date_col, amt_col = mapping.get("date_col"), mapping.get("amount_col")
    grp_col = mapping.get("group_col")
    if not amt_col or amt_col not in df.columns:
        nums = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        amt_col = nums[0] if nums else None
    if not amt_col:
        return {"error": "Tidak ada kolom nominal untuk analisis cashflow.", "findings": []}

    work = df.copy()
    work["_amt"] = coerce_numeric(work[amt_col])

    # Pisahkan arah: kolom tipe (masuk/keluar) atau tanda negatif
    dir_col = None
    for c in df.columns:
        if str(c).lower() in ("tipe", "type", "jenis", "arah", "keterangan_jenis", "arus", "kategori"):
            vals = df[c].astype(str).str.lower()
            if vals.str.contains("masuk|inflow|income|debit|pemasukan").any() and vals.str.contains("keluar|outflow|expense|kredit|pengeluaran").any():
                dir_col = c
                break
    if dir_col:
        v = work[dir_col].astype(str).str.lower()
        work["_in"] = work["_amt"].where(v.str.contains("masuk|inflow|income|debit|pemasukan"), 0).fillna(0)
        work["_out"] = work["_amt"].where(v.str.contains("keluar|outflow|expense|kredit|pengeluaran"), 0).fillna(0)
    else:
        work["_in"] = work["_amt"].where(work["_amt"] >= 0, 0).fillna(0)
        work["_out"] = (-work["_amt"]).where(work["_amt"] < 0, 0).fillna(0)
        if (work["_out"] == 0).all() and (work["_in"] > 0).all():
            # Data hanya pengeluaran positif tanpa arah → anggap outflow bila ada kolom kategori pengeluaran
            pass

    total_in, total_out = float(work["_in"].sum()), float(work["_out"].sum())
    out.update({"total_in": total_in, "total_out": total_out, "net": total_in - total_out})

    trend = []
    if date_col and date_col in df.columns:
        work["_date"] = coerce_date(work[date_col])
        wd = work.dropna(subset=["_date"])
        if len(wd) >= 2:
            g = wd.groupby(pd.Grouper(key="_date", freq="ME"))[["_in", "_out"]].sum()
            g["saldo"] = (g["_in"] - g["_out"]).cumsum()
            trend = [{"periode": d.strftime("%Y-%m"), "masuk": float(r["_in"]), "keluar": float(r["_out"]), "saldo_kumulatif": float(r["saldo"])} for d, r in g.iterrows()]
            # Proyeksi sederhana: moving average 3 periode net
            net = (g["_in"] - g["_out"])
            out["ma3_net"] = float(net.tail(3).mean()) if len(net) >= 1 else 0.0
            out["deficit_risk"] = bool((net.tail(3) < 0).any()) if len(net) >= 1 else False
    out["trend"] = trend

    if grp_col and grp_col in df.columns:
        g = work.groupby(grp_col)[["_in", "_out"]].sum().sort_values("_out", ascending=False)
        out["top_expense"] = [{"nama": str(i), "keluar": float(r["_out"]), "masuk": float(r["_in"])} for i, r in g.head(5).iterrows()]
    else:
        out["top_expense"] = []

    findings = [f"Arus masuk {total_in:,.0f}, arus keluar {total_out:,.0f}, net {total_in - total_out:,.0f}."]
    if out.get("deficit_risk"):
        findings.append("Indikasi potensi defisit: net negatif pada 3 periode terakhir (moving average).")
    if out.get("top_expense"):
        t0 = out["top_expense"][0]
        findings.append(f"Kategori pengeluaran terbesar: {t0['nama']} ({t0['keluar']:,.0f}).")
    if trend and len(trend) >= 2:
        findings.append(f"Tren {len(trend)} periode bulanan tersedia; proyeksi sederhana (MA-3) net {out.get('ma3_net', 0):,.0f}.")
    out["findings"] = findings
    return out
