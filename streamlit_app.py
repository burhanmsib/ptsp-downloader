import streamlit as st
from datetime import datetime

# from modules.backup import run_backup
from modules.backup import run_backup


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="PTSP Downloader BMKG",
    page_icon="📁",
    layout="wide"
)

# =====================================================
# HEADER
# =====================================================

st.title("📁 PTSP Downloader BMKG")

st.caption(
    "Backup otomatis PDF PTSP ke Google Drive dan Google Sheet"
)

st.divider()

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.header("Konfigurasi")

    username = st.text_input(
        "Username PTSP"
    )

    password = st.text_input(
        "Password PTSP",
        type="password"
    )

    bulan = st.text_input(
        "Bulan (YYYY-MM)",
        datetime.now().strftime("%Y-%m")
    )

    st.info(
        "Contoh format bulan:\n\n2026-05"
    )

# =====================================================
# VALIDASI
# =====================================================

if not username or not password:

    st.warning(
        "Silakan isi Username dan Password PTSP terlebih dahulu."
    )

    st.stop()

# =====================================================
# TOMBOL BACKUP
# =====================================================

if st.button(
    "🚀 Mulai Backup",
    use_container_width=True
):

    progress = st.progress(0)

    status = st.empty()

    log_box = st.empty()

    logs = []

    def log(text):

        logs.append(text)

        log_box.code(
            "\n".join(logs),
            language="text"
        )

    try:

        status.info("Menjalankan proses backup...")

        progress.progress(10)

        hasil = run_backup(

            bulan=bulan,

            username=username,

            password=password,

            log=log

        )

        progress.progress(100)

        status.success("Backup selesai")

        st.divider()

        st.subheader("Ringkasan Backup")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Total",
            hasil["total"]
        )

        col2.metric(
            "Uploaded",
            hasil["uploaded"]
        )

        col3.metric(
            "Waiting",
            hasil["waiting"]
        )

        col4.metric(
            "Skip",
            hasil["skip"]
        )

        col5.metric(
            "Error",
            hasil["error"]
        )

    except Exception as e:

        progress.empty()

        status.error(str(e))
