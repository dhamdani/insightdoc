"""InsightDoc MVP — alur PRD §5: Login → Upload → Deteksi&Konfirmasi →
Mapping → Analisis → Dashboard → Unduh → Riwayat&Perbandingan.
Dwibahasa ID/EN (FR-16a)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from insightdoc import auth
from insightdoc.detection import detect_category, suggest_mapping
from insightdoc.engine import run_analysis
from insightdoc.i18n import CATEGORIES, t
from insightdoc.parsing import parse_and_merge
from insightdoc.reports import build_docx, build_pdf
from insightdoc.storage import delete_document, get_document, list_documents, save_document

st.set_page_config(page_title="InsightDoc", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "id"
if "user" not in st.session_state:
    st.session_state.user = None
lang = st.session_state.lang

with st.sidebar:
    st.title("InsightDoc")
    st.session_state.lang = st.radio("Bahasa / Language", ["id", "en"],
                                     format_func=lambda x: "Indonesia" if x == "id" else "English",
                                     index=0 if lang == "id" else 1)
    lang = st.session_state.lang
    if st.session_state.user:
        st.write(f"👤 {st.session_state.user['email']}")
        if st.button("Keluar / Sign out"):
            st.session_state.user = None
            st.rerun()

st.title(t("app_title", lang))

# ---- Auth (FR-20/21) ----
if not st.session_state.user:
    tab_login, tab_reg = st.tabs([t("login", lang), t("register", lang)])
    with tab_login:
        e = st.text_input(t("email", lang), key="li_e")
        p = st.text_input(t("password", lang), type="password", key="li_p")
        if st.button(t("login", lang)):
            u = auth.login(e, p)
            if u:
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Login gagal / Failed.")
    with tab_reg:
        e = st.text_input(t("email", lang), key="rg_e")
        n = st.text_input(t("name", lang), key="rg_n")
        d = st.text_input(t("department", lang), key="rg_d")
        p = st.text_input(t("password", lang), type="password", key="rg_p")
        if st.button(t("register", lang)):
            try:
                auth.register(e, p, n, d)
                st.success("Terdaftar. Silakan masuk. / Registered. Please sign in.")
            except ValueError as ex:
                st.error(str(ex))
    st.stop()

user = st.session_state.user
menu = st.sidebar.radio("Menu", [t("upload", lang), t("history", lang), t("compare", lang)])

# ============ UPLOAD & ANALISIS ============
if menu == t("upload", lang):
    files = st.file_uploader("CSV / XLSX / XLS / PDF (maks 20MB/file, multi-file OK)",
                             accept_multiple_files=True, type=["csv", "xlsx", "xls", "pdf"])
    if files:
        raw = [(f.name, f.getvalue()) for f in files]
        try:
            with st.spinner("Parsing dokumen..."):
                df, notes = parse_and_merge(raw)
        except Exception as e:
            st.error(f"Gagal parsing / Parse failed: {e}")
            df = None
        if df is not None:
            st.info("\n".join(notes))
            st.dataframe(df.head(20), use_container_width=True)

            det = detect_category(df)
            st.write(f"Deteksi otomatis: **{CATEGORIES[det['category']][lang]}** "
                     f"(confidence {det['confidence']}, skor {det['scores']})")
            cat = st.selectbox(t("category", lang), list(CATEGORIES),
                               format_func=lambda c: CATEGORIES[c][lang],
                               index=list(CATEGORIES).index(det["category"]))

            sugg = suggest_mapping(df, cat)
            cols = ["—"] + list(df.columns)
            def pick(label, default):
                idx = cols.index(default) if default in cols else 0
                v = st.selectbox(label, cols, index=idx)
                return None if v == "—" else v
            c1, c2 = st.columns(2)
            with c1:
                date_col = pick("Kolom tanggal / Date column", sugg.get("date_col"))
                amount_col = pick("Kolom nominal / Amount column", sugg.get("amount_col"))
            with c2:
                group_col = pick("Kolom grup / Group column", sugg.get("group_col"))
                qty_col = pick("Kolom qty (opsional)", sugg.get("qty_col"))
            mapping = {"date_col": date_col, "amount_col": amount_col,
                       "group_col": group_col, "qty_col": qty_col}

            extra = st.text_area("Catatan tambahan sebelum unduh (FR-15) / Extra notes",
                                 placeholder="Mis. konteks promo bulan lalu...")

            if st.button("Jalankan analisis / Run analysis"):
                with st.spinner("Menganalisis..."):
                    analysis = run_analysis(df, category=cat, mapping=mapping, lang=lang)
                st.session_state.last_analysis = analysis
                st.session_state.last_files = "+".join(f.name for f in files)
                doc_id = save_document(user["email"], st.session_state.last_files,
                                       analysis["category"], analysis["n_rows"], analysis)
                st.session_state.last_doc_id = doc_id
                st.success(f"Tersimpan sebagai dokumen #{doc_id}")

    ana = st.session_state.get("last_analysis")
    if ana:
        st.header(t("executive_summary", lang))
        st.write(ana["executive_summary"])
        st.header(t("key_findings", lang))
        for f in (ana.get("result") or {}).get("findings", []):
            st.markdown(f"- {f}")
        st.header(t("recommendations", lang))
        for r in ana.get("recommendations", []):
            color = {"Tinggi": "🔴", "Sedang": "🟡"}.get(r["prioritas"], "🟢")
            st.markdown(f"{color} **[{r['prioritas']}]** {r['teks']}\n\n*Alasan: {r['alasan']}*")
        with st.expander(t("data_appendix", lang)):
            st.json({"cleaning": ana.get("cleaning"), "mapping": ana.get("mapping")})
        c1, c2 = st.columns(2)
        extra = st.session_state.get("extra_notes", "")
        with c1:
            st.download_button(t("download_pdf", lang), build_pdf(ana, extra),
                               file_name=f"insightdoc_{ana['category']}.pdf", mime="application/pdf")
        with c2:
            st.download_button(t("download_docx", lang), build_docx(ana, extra),
                               file_name=f"insightdoc_{ana['category']}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ============ RIWAYAT (FR-17/19) ============
elif menu == t("history", lang):
    st.header(t("history", lang))
    docs = list_documents(user["email"])
    if not docs:
        st.info("Belum ada laporan. / No reports yet.")
    for d in docs:
        with st.expander(f"#{d['id']} {d['filename']} [{d['category']}] n={d['n_rows']}"):
            full = get_document(d["id"])
            ana = full.get("analysis", {}) if full else {}
            if ana:
                st.write(ana.get("executive_summary", ""))
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.download_button(t("download_pdf", lang), build_pdf(ana),
                                       file_name=f"insightdoc_{d['id']}.pdf", key=f"pdf{d['id']}")
                with c2:
                    st.download_button(t("download_docx", lang), build_docx(ana),
                                       file_name=f"insightdoc_{d['id']}.docx", key=f"docx{d['id']}")
                with c3:
                    if st.button("Hapus / Delete", key=f"del{d['id']}"):
                        delete_document(d["id"], user["email"])
                        st.rerun()

# ============ BANDINGKAN PERIODE (FR-18) ============
else:
    st.header(t("compare", lang))
    docs = list_documents(user["email"])
    if len(docs) < 2:
        st.info("Butuh minimal 2 laporan tersimpan untuk perbandingan. / Need at least 2 saved reports.")
    else:
        opts = {f"#{d['id']} {d['filename']} [{d['category']}]": d["id"] for d in docs}
        a = st.selectbox("Periode A", list(opts), index=0)
        b = st.selectbox("Periode B", list(opts), index=1)
        if st.button("Bandingkan / Compare"):
            da, db = get_document(opts[a]), get_document(opts[b])
            aa, ab = da["analysis"], db["analysis"]
            if aa.get("category") != ab.get("category"):
                st.warning("Kategori berbeda — perbandingan hanya valid bila kategori sama (FR-18). / Different categories.")
            fa = (aa.get("result") or {}).get("findings", [])
            fb = (ab.get("result") or {}).get("findings", [])
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(a)
                st.write(aa.get("executive_summary", ""))
                for f in fa:
                    st.markdown(f"- {f}")
            with col2:
                st.subheader(b)
                st.write(ab.get("executive_summary", ""))
                for f in fb:
                    st.markdown(f"- {f}")
