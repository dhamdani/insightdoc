"""Pembersihan data dasar otomatis (FR-4)."""
from __future__ import annotations

import pandas as pd


def cleaning_report(df: pd.DataFrame) -> dict:
    dup = int(df.duplicated().sum())
    null_cells = int(df.isna().sum().sum())
    null_cols = {c: int(df[c].isna().sum()) for c in df.columns if int(df[c].isna().sum()) > 0}
    # Deteksi format tanggal tidak konsisten
    date_issues = []
    for c in df.columns:
        if "tanggal" in c.lower() or "date" in c.lower() or "tgl" in c.lower():
            parsed = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
            bad = int(parsed.isna().sum() - df[c].isna().sum())
            if bad > 0:
                date_issues.append(f"Kolom '{c}': {bad} nilai tanggal tidak konsisten")
    return {
        "rows": len(df),
        "cols": len(df.columns),
        "duplicate_rows": dup,
        "null_cells": null_cells,
        "null_per_column": null_cols,
        "date_issues": date_issues,
    }


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Bersihkan ringan: hapus duplikat & baris kosong penuh. Nilai kosong dibiarkan untuk transparansi."""
    df = df.drop_duplicates().dropna(how="all").reset_index(drop=True)
    return df


def coerce_numeric(series: pd.Series) -> pd.Series:
    """Konversi angka toleran format Indonesia (1.234,56 / Rp)."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    s = series.astype(str).str.strip()
    s = s.str.replace(r"(?i)\brp\.?\b", "", regex=True).str.strip()
    # Jika ada koma desimal ala ID (1.234,56)
    has_id_decimal = s.str.contains(r"\d\.\d{3},\d", regex=True, na=False).any()
    if has_id_decimal:
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    else:
        # koma sebagai pemisah ribuan en
        s = s.str.replace(",", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def coerce_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", dayfirst=True)
