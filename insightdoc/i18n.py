"""Dwibahasa (ID/EN) untuk UI dan laporan. Sejak Fase 1 wajib bilingual (PRD §8)."""

STRINGS = {
    "app_title": {"id": "InsightDoc — Analisis Dokumen Bisnis Otomatis", "en": "InsightDoc — Automatic Business Document Analysis"},
    "login": {"id": "Masuk", "en": "Sign in"},
    "register": {"id": "Daftar", "en": "Sign up"},
    "email": {"id": "Email perusahaan", "en": "Company email"},
    "password": {"id": "Kata sandi", "en": "Password"},
    "name": {"id": "Nama", "en": "Name"},
    "department": {"id": "Departemen", "en": "Department"},
    "upload": {"id": "Unggah Dokumen", "en": "Upload Documents"},
    "category": {"id": "Kategori", "en": "Category"},
    "executive_summary": {"id": "Ringkasan Eksekutif", "en": "Executive Summary"},
    "key_findings": {"id": "Temuan Utama", "en": "Key Findings"},
    "visualization": {"id": "Visualisasi Data", "en": "Data Visualization"},
    "recommendations": {"id": "Rekomendasi Tindakan", "en": "Action Recommendations"},
    "data_appendix": {"id": "Lampiran Data", "en": "Data Appendix"},
    "download_pdf": {"id": "Unduh PDF", "en": "Download PDF"},
    "download_docx": {"id": "Unduh Word", "en": "Download Word"},
    "history": {"id": "Riwayat", "en": "History"},
    "compare": {"id": "Bandingkan Periode", "en": "Compare Periods"},
    "priority_high": {"id": "Prioritas Tinggi", "en": "High Priority"},
    "priority_medium": {"id": "Prioritas Sedang", "en": "Medium Priority"},
    "priority_low": {"id": "Prioritas Rendah", "en": "Low Priority"},
    "finding": {"id": "Temuan", "en": "Finding"},
    "recommendation": {"id": "Rekomendasi", "en": "Recommendation"},
    "reason": {"id": "Alasan/Data pendukung", "en": "Rationale/Supporting data"},
}

CATEGORIES = {
    "penjualan": {"id": "Penjualan", "en": "Sales"},
    "karyawan": {"id": "Karyawan / HR", "en": "Employees / HR"},
    "cashflow": {"id": "Cashflow / Keuangan", "en": "Cashflow / Finance"},
    "umum": {"id": "Umum / Lainnya", "en": "General / Other"},
}


def t(key: str, lang: str = "id") -> str:
    lang = "en" if lang == "en" else "id"
    return STRINGS.get(key, {}).get(lang, key)


def cat_label(cat: str, lang: str = "id") -> str:
    lang = "en" if lang == "en" else "id"
    return CATEGORIES.get(cat, {}).get(lang, cat)
