"""Rekomendasi tindakan berbasis aturan (PRD §7).

Prinsip: setiap insight signifikan → ≥1 rekomendasi spesifik + prioritas +
alasan/data pendukung, bahasa praktis. AI generatif hanya menyusun narasi;
angka berasal dari perhitungan deterministik (guardrail ambang data minimum).
"""
from __future__ import annotations


def _rec(teks_id: str, teks_en: str, prioritas: str, alasan: str, lang: str = "id") -> dict:
    return {
        "teks": teks_id if lang == "id" else teks_en,
        "prioritas": prioritas,  # Tinggi/Sedang/Rendah
        "alasan": alasan,
    }


def recommend_sales(res: dict, lang: str = "id") -> list[dict]:
    recs: list[dict] = []
    n = res.get("n_rows", 0)
    if n < 5:
        return [_rec("Data terlalu sedikit — kumpulkan minimal 5 baris transaksi sebelum menarik kesimpulan tren.",
                     "Too little data — collect at least 5 transaction rows before drawing trend conclusions.",
                     "Rendah", f"n={n} < 5 (guardrail)", lang)]
    g = res.get("mom_growth_pct")
    if g is not None and g <= -10:
        recs.append(_rec(
            f"Penjualan turun {abs(g)}% periode terakhir. Evaluasi harga/stok produk lemah dan pertimbangkan promo bundling dengan produk terlaris.",
            f"Sales dropped {abs(g)}% last period. Review pricing/stock of weak products and consider bundling promos with best sellers.",
            "Tinggi", f"MoM growth {g}%", lang))
    elif g is not None and g >= 10:
        recs.append(_rec(
            f"Penjualan naik {g}%. Tambah stok produk terlaris dan dokumentasikan pendorong pertumbuhan untuk direplikasi.",
            f"Sales grew {g}%. Restock best sellers and document growth drivers to replicate.",
            "Sedang", f"MoM growth {g}%", lang))
    top = res.get("top_groups") or []
    if top:
        t0 = top[0]
        if t0.get("share_pct", 0) >= 50:
            recs.append(_rec(
                f"Ketergantungan tinggi pada {t0['nama']} ({t0['share_pct']}% total). Diversifikasi dengan mengangkat produk lapis kedua.",
                f"High dependence on {t0['nama']} ({t0['share_pct']}% of total). Diversify by promoting second-tier products.",
                "Sedang", f"share {t0['share_pct']}%", lang))
    bot = res.get("bottom_groups") or []
    if bot:
        recs.append(_rec(
            f"Tinjau produk/segmen terlemah ({bot[0]['nama']}). Putuskan: perbaiki (harga/packaging/distribusi) atau hentikan bila 3 periode tak membaik.",
            f"Review weakest segment ({bot[0]['nama']}). Decide: fix (price/packaging/distribution) or discontinue if no improvement for 3 periods.",
            "Sedang", "bottom performer", lang))
    if res.get("outliers"):
        recs.append(_rec(
            f"Ada {len(res['outliers'])} transaksi anomali besar. Verifikasi keabsahan (bukan input ganda/salah) lalu pelajari polanya.",
            f"There are {len(res['outliers'])} large anomalous transactions. Verify validity (not duplicates/errors) then study the pattern.",
            "Rendah", f"{len(res['outliers'])} outliers", lang))
    if not recs:
        recs.append(_rec("Kinerja stabil. Tetapkan target pertumbuhan kecil terukur dan pantau mingguan.",
                         "Performance is stable. Set a small measurable growth target and monitor weekly.",
                         "Rendah", "no significant delta", lang))
    return recs


def recommend_hr(res: dict, lang: str = "id") -> list[dict]:
    recs: list[dict] = []
    t = res.get("turnover_rate_pct")
    if t is not None and t >= 10:
        recs.append(_rec(
            f"Turnover {t}% tergolong tinggi. Lakukan exit interview terstruktur dan tinjau beban kerja/kompensasi di unit dengan keluar terbanyak.",
            f"Turnover at {t}% is high. Run structured exit interviews and review workload/compensation in units with most exits.",
            "Tinggi", f"turnover {t}%", lang))
    sal = res.get("salary") or {}
    if sal.get("max_to_mean_ratio", 0) > 3:
        recs.append(_rec(
            "Indikasi ketimpangan gaji (maks >3x rata-rata). Audit struktur grading dan bandingkan dengan benchmark pasar.",
            "Possible pay inequity (max >3x mean). Audit salary grading against market benchmarks.",
            "Sedang", f"ratio {sal.get('max_to_mean_ratio')}", lang))
    dept = res.get("dept_dist") or []
    if dept and len(dept) >= 2 and dept[0]["jumlah"] >= 2 * dept[1]["jumlah"]:
        recs.append(_rec(
            f"Distribusi timpang: {dept[0]['nama']} jauh terbesar. Cek beban kerja dan risiko single-point-of-failure.",
            f"Skewed distribution: {dept[0]['nama']} dominates. Check workload and single-point-of-failure risk.",
            "Rendah", "dept skew", lang))
    tenure = res.get("tenure") or {}
    if tenure and tenure.get("mean_years", 99) < 1.5:
        recs.append(_rec(
            "Rata-rata masa kerja <1,5 tahun. Perkuat onboarding 90 hari dan program retensi karyawan baru.",
            "Average tenure <1.5 years. Strengthen 90-day onboarding and new-hire retention.",
            "Sedang", f"tenure {tenure.get('mean_years')}y", lang))
    if not recs:
        recs.append(_rec("Kondisi SDM relatif sehat. Lanjutkan survei engagement berkala dan dokumentasikan praktik terbaik retensi.",
                         "Workforce looks healthy. Continue periodic engagement surveys and document retention best practices.",
                         "Rendah", "no red flag", lang))
    return recs


def recommend_cashflow(res: dict, lang: str = "id") -> list[dict]:
    recs: list[dict] = []
    if res.get("deficit_risk"):
        recs.append(_rec(
            "Risiko defisit kas terdeteksi (net negatif recent). Audit pos pengeluaran terbesar dan tunda belanja non-kritis; percepat penagihan piutang.",
            "Cash deficit risk detected (recent negative net). Audit largest expense items, defer non-critical spend, accelerate receivables.",
            "Tinggi", "MA-3 net negatif", lang))
    top = res.get("top_expense") or []
    if top:
        recs.append(_rec(
            f"Pengeluaran terbesar di {top[0]['nama']} ({top[0]['keluar']:,.0f}). Bandingkan dengan anggaran dan cari efisiensi 5–10%.",
            f"Largest expense in {top[0]['nama']} ({top[0]['keluar']:,.0f}). Compare to budget and seek 5–10% efficiency.",
            "Sedang", "top expense", lang))
    if res.get("net", 0) > 0:
        recs.append(_rec(
            "Net positif. Sisihkan cadangan kas 1–3 bulan biaya operasional sebelum ekspansi.",
            "Net positive. Set aside 1–3 months of operating costs as cash reserve before expanding.",
            "Rendah", f"net {res.get('net'):,.0f}", lang))
    if not recs:
        recs.append(_rec("Pantau arus kas mingguan dan tetapkan ambang peringatan saldo minimum.",
                         "Monitor cashflow weekly and set a minimum-balance alert threshold.",
                         "Rendah", "default", lang))
    return recs


def recommend_general(res: dict, lang: str = "id") -> list[dict]:
    recs: list[dict] = []
    for p in (res.get("strong_correlations") or [])[:2]:
        recs.append(_rec(
            f"Korelasi kuat {p['a']} ↔ {p['b']} (r={p['corr']}). Selidiki hubungan sebab-akibat sebelum dijadikan dasar keputusan.",
            f"Strong correlation {p['a']} ↔ {p['b']} (r={p['corr']}). Investigate causation before acting on it.",
            "Sedang", f"r={p['corr']}", lang))
    if not recs:
        recs.append(_rec("Data deskriptif siap. Tentukan 1–2 KPI utama dan pantau per periode berikutnya.",
                         "Descriptive data ready. Define 1–2 key KPIs and track them next periods.",
                         "Rendah", "default", lang))
    return recs


def build_recommendations(category: str, result: dict, lang: str = "id") -> list[dict]:
    fn = {"penjualan": recommend_sales, "karyawan": recommend_hr,
          "cashflow": recommend_cashflow, "umum": recommend_general}.get(category, recommend_general)
    return fn(result, lang)
