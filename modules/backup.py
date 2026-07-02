from datetime import datetime
import os
import streamlit as st
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
    client = None

    client = PTSPClient(
    
        username=username,
    
        password=password,
    
        log=log
    
    )

    summary = {
        "total": 0,
        "uploaded": 0,
        "waiting": 0,
        "skip": 0,
        "error": 0
    }

    try:

        log("=" * 80)
        log("MEMULAI BACKUP PTSP")
        log("=" * 80)

        client.start()

        log("✅ Browser berhasil dijalankan")

        client.login()

        log("✅ Login PTSP berhasil")

        client.open_orders()

        log("✅ Halaman Order berhasil dibuka")

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
        log("✅ Google Sheet terkoneksi")

        log("✅ Google Drive terkoneksi")

        client.search_month(bulan)

        log(f"📅 Bulan pencarian : {bulan}")

        total_pages = client.get_total_pages()

        log(f"📄 Total halaman : {total_pages}")

        for page in range(total_pages):

            log("")
            log("=" * 80)
            log(f"PAGE {page + 1} / {total_pages}")
            log("=" * 80)

            client.goto_page(page)

            orders = client.get_orders()

            log(f"Jumlah order : {len(orders)}")

            for order in orders:

                summary["total"] += 1

                log("-" * 60)
                log(f"Nomor : {order['nomor']}")

                row = sheet.find_order(order["nomor"])

                if row is not None:

                    summary["skip"] += 1

                    log("⏭ Sudah pernah diproses")

                    continue

                client.open_detail(order)

                hasil = client.get_pdf_url()

                if hasil["status"] == "WAITING":

                    sheet.insert(
                        order,
                        "WAITING"
                    )

                    summary["waiting"] += 1

                    log("⌛ PDF belum tersedia")

                    continue

                log("⬇ Download PDF...")

                file_pdf = downloader.download(
                    order,
                    hasil["pdf_url"]
                )

                log("☁ Upload Google Drive...")

                drive_link = drive.upload(
                    file_pdf,
                    order["tanggal_permohonan"]
                )

                sheet.insert(
                    order,
                    "UPLOADED"
                )

                row = sheet.find_order(order["nomor"])

                waktu = datetime.now().strftime(

                    "%Y-%m-%d %H:%M:%S"
                
                )
                
                sheet.update(
                
                    row,
                
                    nama_file=os.path.basename(file_pdf),
                
                    status="UPLOADED",
                
                    google_drive=drive_link,
                
                    pdf_url=hasil["pdf_url"],
                
                    waktu_download=waktu,
                
                    last_check=waktu
                
                )
                summary["uploaded"] += 1

                log("✅ Selesai")
                try:

                    os.remove(file_pdf)
                
                    log("🗑 File sementara dihapus")
                
                except Exception:
                
                    pass

    except Exception as e:

        summary["error"] += 1

        log("")
        log("❌ ERROR")
        log(str(e))

        raise

    finally:

        if client is not None:
    
            try:
    
                client.close()
    
                log("🔒 Browser ditutup")
    
            except Exception:
    
                pass
    
        log("")
        log("=" * 80)
        log("RINGKASAN")
        log("=" * 80)
        log(f"Total Order : {summary['total']}")
        log(f"Uploaded    : {summary['uploaded']}")
        log(f"Waiting     : {summary['waiting']}")
        log(f"Skip        : {summary['skip']}")
        log(f"Error       : {summary['error']}")
    
        if summary["error"] == 0:
    
            log("")
            log("🎉 Backup selesai tanpa error")
    
        else:
    
            log("")
            log("⚠ Backup selesai dengan beberapa error")

    return summary
