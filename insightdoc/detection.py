"""Deteksi kategori dokumen + saran column mapping (FR-5/6/7)."""
from __future__ import annotations

import re

import pandas as pd

KEYWORDS = {
    "penjualan": [
        "penjualan", "sales", "produk", "product", "pelanggan", "customer", "order",
        "transaksi", "transaction", "qty", "quantity", "harga", "price", "total",
        "omzet", "revenue", "toko", "cabang", "wilayah", "region", "kategori",
    ],
    "karyawan": [
        "karyawan", "employee", "pegawai", "nama", "nik", "nip", "departemen",
        "department", "divisi", "jabatan", "position", "gaji", "salary", "upah",
        "absensi", "attendance", "cuti", "leave", "turnover", "masuk", "keluar",
        "tanggal_masuk", "join", "status", "kontrak", "tetap",
    ],
    "cashflow": [
        "cashflow", "cash", "kas", "arus", "pemasukan", "pengeluaran", "income",
        "expense", "debit", "kredit", "saldo", "balance", "keuangan", "finance",
        "anggaran", "budget", "operasional", "inflow", "outflow", "nominal",
        "tipe", "jenis_bayar", "keterangan",
    ],
}

DATE_HINTS = ["tanggal", "date", "tgl", "periode", "period", "bulan", "month", "tahun", "year", "waktu", "time"]
AMOUNT_HINTS = ["nominal", "jumlah", "amount", "total", "nilai", "value", "harga", "price", "gaji", "salary", "omzet", "revenue"]
GROUP_HINTS = ["produk", "product", "kategori", "category", "departemen", "department", "cabang", "branch", "wilayah", "region", "karyawan", "employee"]


def _norm(cols: list[str]) -> list[str]:
    return [re.sub(r"[^a-z0-9]+", " ", str(c).lower()).strip() for c in cols]


def detect_category(df: pd.DataFrame) -> dict:
    cols = _norm(list(df.columns))
    joined = " ".join(cols)
    scores = {}
    for cat, kws in KEYWORDS.items():
        scores[cat] = sum(1 for k in kws if k in joined)
    # Tie-break berbasis isi sel (mis. kolom tipe berisi masuk/keluar → cashflow)
    try:
        sample = df.head(50).astype(str).apply(lambda s: " ".join(s.str.lower().tolist()))
        blob = " ".join(sample.tolist())
        if any(w in blob for w in ("masuk", "keluar", "inflow", "outflow", "defisit", "operasional")):
            scores["cashflow"] = scores.get("cashflow", 0) + 2
        if any(w in blob for w in ("resign", "turnover", "departemen", "jabatan", "onboarding")):
            scores["karyawan"] = scores.get("karyawan", 0) + 2
    except Exception:
        pass
    best = max(scores, key=lambda k: scores[k])
    total = sum(scores.values())
    confidence = round(scores[best] / max(total, 1), 2) if total else 0.0
    if scores[best] == 0:
        best, confidence = "umum", 0.0
    return {"category": best, "confidence": confidence, "scores": scores}


def suggest_mapping(df: pd.DataFrame, category: str) -> dict:
    """Saran mapping kolom → peran analisis. Bisa dikonfirmasi/diedit user (FR-7)."""
    mapping: dict[str, str | None] = {"date_col": None, "amount_col": None, "group_col": None, "qty_col": None}
    cols = list(df.columns)
    low = {c: str(c).lower() for c in cols}

    def find(hints: list[str]) -> str | None:
        for c in cols:
            if any(h in low[c] for h in hints):
                return c
        return None

    mapping["date_col"] = find(DATE_HINTS)
    mapping["amount_col"] = find(AMOUNT_HINTS)
    mapping["group_col"] = find(GROUP_HINTS)
    for c in cols:
        if low[c] in ("qty", "quantity", "jumlah", "unit", "pcs"):
            mapping["qty_col"] = c
            break

    # Fallback berbasis tipe data
    if mapping["date_col"] is None:
        for c in cols:
            parsed = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
            if parsed.notna().mean() > 0.6:
                mapping["date_col"] = c
                break
    if mapping["amount_col"] is None:
        nums = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
        if nums:
            mapping["amount_col"] = nums[0]
    return mapping
