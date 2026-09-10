"""Uji MVP InsightDoc: deteksi, analisis, rekomendasi, parsing, laporan."""
import io

import pandas as pd

from insightdoc.detection import detect_category
from insightdoc.engine import run_analysis
from insightdoc.parsing import parse_and_merge, ParseError
from insightdoc.reports import build_docx, build_pdf


def df_sales():
    return pd.read_csv("samples/penjualan_sample.csv")


def test_detect_sales():
    assert detect_category(df_sales())["category"] == "penjualan"


def test_detect_hr_cashflow():
    hr = pd.read_csv("samples/karyawan_sample.csv")
    cf = pd.read_csv("samples/cashflow_sample.csv")
    assert detect_category(hr)["category"] == "karyawan"
    assert detect_category(cf)["category"] == "cashflow"


def test_end_to_end_id_en():
    df = df_sales()
    for lang in ("id", "en"):
        ana = run_analysis(df, lang=lang)
        assert ana["category"] == "penjualan"
        assert ana["executive_summary"]
        assert len(ana["recommendations"]) >= 1
        assert all({"teks", "prioritas", "alasan"} <= set(r) for r in ana["recommendations"])
        pdf = build_pdf(ana)
        docx = build_docx(ana)
        assert pdf[:4] == b"%PDF"
        assert docx[:2] == b"PK"


def test_multi_file_merge_and_validation():
    a = open("samples/penjualan_sample.csv", "rb").read()
    df, notes = parse_and_merge([("a.csv", a), ("b.csv", a)])
    assert len(df) == 16
    try:
        parse_and_merge([("x.exe", b"hi")])
        raise AssertionError("harus gagal")
    except ParseError:
        pass


def test_guardrail_small_data():
    df = pd.DataFrame({"produk": ["A"], "total": [100]})
    ana = run_analysis(df, category="penjualan", lang="id")
    assert any("minimal" in r["teks"] or "sedikit" in r["teks"] for r in ana["recommendations"])
