import os
import subprocess

PLAYWRIGHT_PATH = os.path.expanduser("~/.cache/ms-playwright")

if not os.path.exists(PLAYWRIGHT_PATH):
    subprocess.run(
        ["playwright", "install", "chromium"],
        check=False
    )

import streamlit as st
from datetime import datetime

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
    "Backup otomatis dokumen PTSP (PDF, RAR, ZIP, dll) ke Google Drive dan Google Sheet"
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

    def log(*args):

        try:
    
            text = " ".join(map(str, args))
    
        except Exception:
    
            text = str(args)
    
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
            log=log,
            progress=progress,
            status=status
        )

        progress.progress(100)

        status.success(f"Backup bulan {bulan} selesai")

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

        bulan_run = hasil.get("bulan", bulan)

        if hasil["total"] == 0:

            st.info(
                f"Tidak ada order dengan Tanggal Pembayaran {bulan_run}."
            )

        elif hasil["waiting"] == 0 and hasil["error"] == 0:

            st.success(
                f"✅ Semua file bulan {bulan_run} sudah selesai dibackup "
                f"({hasil['total']} order)."
            )

        if hasil.get("non_pdf_list"):

            st.info(
                f"📦 {len(hasil['non_pdf_list'])} dokumen bukan PDF "
                "(mis. RAR/ZIP) ikut disimpan ke folder Drive bulan ini:"
            )

            st.dataframe(
                hasil["non_pdf_list"],
                use_container_width=True
            )

        if hasil.get("waiting_list"):

            st.warning(
                f"⌛ {hasil['waiting']} order bulan {bulan_run} masih WAITING "
                "(dokumen belum diunggah di PTSP). Jalankan lagi bulan "
                f"{bulan_run} nanti untuk mem-backup-nya."
            )

            st.dataframe(
                hasil["waiting_list"],
                use_container_width=True
            )

        if hasil.get("error_list"):

            st.error(
                f"❌ {hasil['error']} order gagal diproses. "
                "Jalankan lagi bulan yang sama untuk mencoba ulang."
            )

            st.dataframe(
                hasil["error_list"],
                use_container_width=True
            )

    except Exception as e:

        progress.empty()

        status.error(str(e))
