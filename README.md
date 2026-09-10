# InsightDoc — Analisis Dokumen Bisnis Otomatis (MVP Fase 1)

Internal tool (satu perusahaan) sesuai PRD v1.1: upload CSV/XLSX/XLS/PDF tabel →
deteksi kategori (penjualan/karyawan/cashflow/umum) → column mapping →
analisis deterministik + rekomendasi berbasis aturan → laporan PDF/Word dwibahasa (ID/EN).

## Struktur
```
doksys/
  app.py                  # Streamlit: login → upload → mapping → dashboard → unduh → riwayat/banding
  insightdoc/             # parsing, detection, cleaning, analysis_*, recommendations, engine, reports, storage, auth, i18n
  tests/                  # pytest
  samples/                # contoh CSV per kategori
  data/                   # SQLite (dibuat otomatis, jangan commit)
```

## Jalankan
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Uji
```bash
pytest -q
```

## Catatan PRD
- Angka laporan selalu dari perhitungan deterministik; rekomendasi berbasis rule+template per kategori (guardrail n minimum).
- FR PDF-tabel kompleks, multi-user departemen/RBAC (Fase 3), forecasting lanjutan: di luar MVP ini.
- Auth MVP: email+password lokal; produksi → SSO korporat (Google Workspace/Microsoft 365).
