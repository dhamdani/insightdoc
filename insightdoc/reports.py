"""Generator laporan PDF & Word (FR-13/14/15) + chart matplotlib.

Struktur: Ringkasan Eksekutif, Temuan Utama, Visualisasi, Rekomendasi, Lampiran.
"""
from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .i18n import cat_label, t


def _chart_trend(analysis: dict) -> bytes | None:
    trend = (analysis.get("result") or {}).get("trend") or []
    if not trend or len(trend) < 2:
        return None
    # Dukung format sales (periode/nilai) & cashflow (periode/masuk/keluar)
    labels = [r.get("periode", "") for r in trend]
    plt.figure(figsize=(7, 3.2))
    if "masuk" in trend[0]:
        plt.plot(labels, [r["masuk"] for r in trend], marker="o", label="Masuk/In")
        plt.plot(labels, [r["keluar"] for r in trend], marker="o", label="Keluar/Out")
        plt.legend()
    else:
        plt.bar(labels, [r.get("nilai", 0) for r in trend])
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130)
    plt.close()
    buf.seek(0)
    return buf.read()


def _chart_top(analysis: dict) -> bytes | None:
    res = analysis.get("result") or {}
    groups = res.get("top_groups") or res.get("dept_dist") or res.get("top_expense")
    if not groups:
        return None
    names = [g.get("nama", "?") for g in groups[:5]]
    vals = [g.get("nilai", g.get("jumlah", g.get("keluar", 0))) for g in groups[:5]]
    plt.figure(figsize=(7, 3.0))
    plt.barh(names[::-1], vals[::-1])
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130)
    plt.close()
    buf.seek(0)
    return buf.read()


def _safe(text: object) -> str:
    if text is None:
        return "-"
    s = str(text)
    return s.encode("latin-1", "replace").decode("latin-1")


def build_pdf(analysis: dict, extra_notes: str = "") -> bytes:
    from fpdf import FPDF

    lang = analysis.get("lang", "id")
    cat = cat_label(analysis.get("category", "umum"), lang)
    pdf = FPDF()
    pdf.set_auto_page_break(True, 20)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, _safe(f"InsightDoc — {cat}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, _safe(f"{t('category', lang)}: {cat} | n={analysis.get('n_rows', 0)}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    def section(title: str, body_lines: list[str]):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, _safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for line in body_lines:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(w=pdf.epw, h=6, text=_safe(f"- {line}"))
        pdf.ln(1)

    res = analysis.get("result") or {}
    section(t("executive_summary", lang), [analysis.get("executive_summary", "") + (f" {extra_notes}" if extra_notes else "")])
    section(t("key_findings", lang), res.get("findings", []) or ["-"])

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 10, _safe(t("visualization", lang)), new_x="LMARGIN", new_y="NEXT")
    for img in (_chart_trend(analysis), _chart_top(analysis)):
        if img:
            tmp = io.BytesIO(img)
            # fpdf butuh file-like dengan ekstensi; simpan sementara via BytesIO + type png
            pdf.set_x(pdf.l_margin)
            pdf.image(tmp, w=min(170, pdf.epw))
            pdf.ln(2)

    rec_lines = [f"[{r['prioritas']}] {r['teks']} (Alasan: {r['alasan']})" for r in analysis.get("recommendations", [])]
    section(t("recommendations", lang), rec_lines or ["-"])

    cl = analysis.get("cleaning", {})
    section(t("data_appendix", lang),
            [f"Baris: {cl.get('rows')}, Kolom: {cl.get('cols')}, Duplikat: {cl.get('duplicate_rows')}, Sel kosong: {cl.get('null_cells')}",
             f"Mapping: {analysis.get('mapping', {})}"])
    return bytes(pdf.output())


def build_docx(analysis: dict, extra_notes: str = "") -> bytes:
    from docx import Document
    from docx.shared import Pt

    lang = analysis.get("lang", "id")
    doc = Document()
    doc.add_heading(f"InsightDoc — {cat_label(analysis.get('category', 'umum'), lang)}", 0)
    doc.add_paragraph(f"{t('category', lang)}: {cat_label(analysis.get('category', 'umum'), lang)} | n={analysis.get('n_rows', 0)}")
    doc.add_heading(t("executive_summary", lang), 1)
    doc.add_paragraph(analysis.get("executive_summary", "") + (f" {extra_notes}" if extra_notes else ""))
    if extra_notes and "Catatan" not in extra_notes:
        pass
    doc.add_heading(t("key_findings", lang), 1)
    for f in (analysis.get("result") or {}).get("findings", []):
        doc.add_paragraph(f, style="List Bullet")
    doc.add_heading(t("visualization", lang), 1)
    for img in (_chart_trend(analysis), _chart_top(analysis)):
        if img:
            doc.add_picture(io.BytesIO(img), width=Pt(430))
    doc.add_heading(t("recommendations", lang), 1)
    for r in analysis.get("recommendations", []):
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(f"[{r['prioritas']}] ").bold = True
        p.add_run(f"{r['teks']} (Alasan: {r['alasan']})")
    doc.add_heading(t("data_appendix", lang), 1)
    doc.add_paragraph(f"Cleaning: {analysis.get('cleaning', {})} | Mapping: {analysis.get('mapping', {})}")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()
