from datetime import datetime
import os

from modules.client import PTSPClient
from modules.download import PDFDownloader
from modules.sheets import SheetManager
from modules.drive import DriveManager


def run_backup(
    bulan,
    username,
    password,
    log=print
):

    summary = {
        "total": 0,
        "uploaded": 0,
        "waiting": 0,
        "skip": 0,
        "error": 0
    }

    client = None

    try:

        log("=" * 80)
        log("🚀 MEMULAI BACKUP PTSP")
        log("=" * 80)

        # ==========================================
        # Client PTSP
        # ==========================================

        client = PTSPClient(

            username=username,

            password=password,

            log=log

        )

        client.start()

        client.login()

        client.open_orders()

        # ==========================================
        # Module
        # ==========================================

        downloader = PDFDownloader(

            client.context,

            log

        )

        sheet = SheetManager(

            log

        )

        drive = DriveManager(

            log

        )

        # ==========================================
        # Cari Bulan
        # ==========================================

        client.search_month(bulan)

        total_pages = client.get_total_pages()

        log(f"📄 Total halaman : {total_pages}")

        # ==========================================
        # Loop halaman
        # ==========================================

        for page in range(total_pages):

            log("")
            log("=" * 80)
            log(f"📄 PAGE {page + 1} / {total_pages}")
            log("=" * 80)

            client.goto_page(page)

            orders = client.get_orders()

            log(f"Jumlah order : {len(orders)}")

            # ======================================
            # Loop Order
            # ======================================

            for order in orders:

                summary["total"] += 1

                log("-" * 60)
                log(f"Nomor : {order['nomor']}")

                row = sheet.find_order(

                    order["nomor"]

                )

                if row is not None:

                    summary["skip"] += 1

                    log("⏭ Sudah pernah diproses")

                    continue

                # ===============================
                # Detail
                # ===============================

                client.open_detail(order)

                hasil = client.get_pdf_url()

                # ===============================
                # PDF BELUM ADA
                # ===============================

                if hasil["status"] == "WAITING":

                    sheet.insert(

                        order,

                        "WAITING"

                    )

                    summary["waiting"] += 1

                    log("⌛ PDF belum tersedia")

                    continue

                # ===============================
                # DOWNLOAD
                # ===============================

                file_pdf = downloader.download(

                    order,

                    hasil["pdf_url"]

                )

                if file_pdf is None:

                    summary["error"] += 1

                    log("❌ Download gagal")

                    continue

                # ===============================
                # UPLOAD DRIVE
                # ===============================

                drive_link = drive.upload(

                    file_pdf,

                    order["tanggal_permohonan"]

                )

                # ===============================
                # INSERT SHEET
                # ===============================

                sheet.insert(

                    order,

                    "UPLOADED"

                )

                row = sheet.find_order(

                    order["nomor"]

                )

                # ===============================
                # UPDATE SHEET
                # ===============================

                sheet.update(

                    row,

                    nama_file=os.path.basename(file_pdf),

                    status="UPLOADED",

                    google_drive=drive_link,

                    pdf_url=hasil["pdf_url"],

                    waktu_download=datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),

                    last_check=datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                )

                summary["uploaded"] += 1

                log("✅ Backup selesai")

    except Exception as e:

        summary["error"] += 1

        log("")
        log("=" * 80)
        log("❌ TERJADI ERROR")
        log("=" * 80)
        log(str(e))

        raise

    finally:

        if client:

            client.close()

        log("")
        log("=" * 80)
        log("📊 RINGKASAN")
        log("=" * 80)
        log(f"Total Order : {summary['total']}")
        log(f"Uploaded    : {summary['uploaded']}")
        log(f"Waiting     : {summary['waiting']}")
        log(f"Skip        : {summary['skip']}")
        log(f"Error       : {summary['error']}")

    return summary