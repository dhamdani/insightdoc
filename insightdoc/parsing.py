"""Parsing dokumen: CSV / XLSX / XLS / PDF tabel → DataFrame terstruktur.

FR-1: .csv, .xlsx, .xls, .pdf (tabel), maks 20MB per file.
FR-2: multi-file digabung dalam satu analisis.
FR-3: validasi awal dengan pesan error jelas.
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

MAX_FILE_MB = 20
ALLOWED_EXT = {".csv", ".xlsx", ".xls", ".pdf"}


class ParseError(ValueError):
    pass


def validate_file(name: str, size_bytes: int) -> None:
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise ParseError(
            f"Format '{ext}' tidak didukung. Gunakan: {', '.join(sorted(ALLOWED_EXT))}. "
            f"Unsupported format '{ext}'. Use: {', '.join(sorted(ALLOWED_EXT))}."
        )
    if size_bytes > MAX_FILE_MB * 1024 * 1024:
        raise ParseError(
            f"File '{name}' melebihi {MAX_FILE_MB}MB. "
            f"File '{name}' exceeds {MAX_FILE_MB}MB."
        )
    if size_bytes == 0:
        raise ParseError(f"File '{name}' kosong. File '{name}' is empty.")


def parse_csv(data: bytes) -> pd.DataFrame:
    for sep in [",", ";", "\t", "|"]:
        try:
            df = pd.read_csv(io.BytesIO(data), sep=sep)
            if len(df.columns) > 1:
                return df
        except Exception:
            continue
    df = pd.read_csv(io.BytesIO(data))
    return df


def parse_excel(data: bytes, ext: str = ".xlsx") -> pd.DataFrame:
    xls = pd.ExcelFile(io.BytesIO(data))
    frames = []
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        df = df.dropna(how="all").dropna(axis=1, how="all")
        if not df.empty:
            frames.append(df)
    if not frames:
        raise ParseError("File Excel kosong / tidak ada sheet terbaca. Excel file is empty.")
    if len(frames) == 1:
        return frames[0]
    # Gabung multi-sheet dengan kolom union
    return pd.concat(frames, ignore_index=True, sort=False)


def parse_pdf_table(data: bytes) -> pd.DataFrame:
    """Ekstrak tabel dari PDF (fase 1: tabel sederhana)."""
    try:
        import pdfplumber
    except ImportError as e:
        raise ParseError("Dukungan PDF belum terinstal (pdfplumber).") from e
    frames = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for tbl in tables:
                if len(tbl) < 2:
                    continue
                header, rows = tbl[0], tbl[1:]
                df = pd.DataFrame(rows, columns=header)
                frames.append(df)
    if not frames:
        raise ParseError(
            "Tidak ada tabel terdeteksi di PDF. Fase awal hanya mendukung PDF bertabel sederhana. "
            "No table detected in PDF. Only simple tabular PDFs are supported."
        )
    df = pd.concat(frames, ignore_index=True)
    df.columns = [str(c).strip() if c else f"col_{i}" for i, c in enumerate(df.columns)]
    return df


def parse_bytes(name: str, data: bytes) -> pd.DataFrame:
    validate_file(name, len(data))
    ext = Path(name).suffix.lower()
    if ext == ".csv":
        df = parse_csv(data)
    elif ext in (".xlsx", ".xls"):
        df = parse_excel(data, ext)
    elif ext == ".pdf":
        df = parse_pdf_table(data)
    else:
        raise ParseError(f"Format tidak didukung: {ext}")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    if df.empty:
        raise ParseError(f"File '{name}' tidak berisi baris data. File '{name}' has no data rows.")
    if len(df.columns) == 0:
        raise ParseError(f"Kolom tidak terbaca di '{name}'. Columns unreadable in '{name}'.")
    return df


def parse_and_merge(files: list[tuple[str, bytes]]) -> tuple[pd.DataFrame, list[str]]:
    """Gabung banyak file (FR-2). Kembalikan (df_gabung, catatan)."""
    if not files:
        raise ParseError("Tidak ada file diunggah. No files uploaded.")
    frames, notes = [], []
    for name, data in files:
        df = parse_bytes(name, data)
        df["_sumber_file"] = name
        frames.append(df)
        notes.append(f"{name}: {len(df)} baris, {len(df.columns)} kolom")
    if len(frames) == 1:
        merged = frames[0]
    else:
        merged = pd.concat(frames, ignore_index=True, sort=False)
        notes.append(f"Digabung: {len(merged)} baris total dari {len(frames)} file.")
    return merged, notes
