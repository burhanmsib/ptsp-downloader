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
    log=print,
    progress=None,
    status=None
):
    # client = None

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

        log(f"📅 Bulan pencarian : {bulan}")

        log("📋 Mengumpulkan seluruh order...")
        
        orders = client.collect_all_orders(bulan)
        total_orders = len(orders)
        
        log(f"📄 Total order ditemukan : {len(orders)}")

        for order in orders:

            try:
        
                summary["total"] += 1
        
                log("-" * 60)
                log(f"Nomor : {order['nomor']}")
        
                row = sheet.find_order(order["nomor"])
        
                if row is not None:
        
                    summary["skip"] += 1
        
                    log("⏭ Sudah pernah diproses")
        
                    continue
        
                log(f"🌐 Membuka {order['detail']}")
                
                client.open_detail(order)
        
                hasil = client.get_pdf_url()
        
                if hasil["status"] == "READY" and not hasil["pdf_url"]:

                    raise Exception("PDF URL kosong.")
        
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

                if not os.path.exists(file_pdf):

                    raise Exception("File PDF tidak ditemukan setelah download.")
        
                log("☁ Upload Google Drive...")
        
                drive_link = drive.upload(
                    file_pdf,
                    order["tanggal_permohonan"]
                )

                if not drive_link:

                    raise Exception("Upload Google Drive gagal.")
        
                sheet.insert(
                    order,
                    "UPLOADED"
                )
                
                row = sheet.find_order(order["nomor"])
                
                if row is None:
                
                    raise Exception(
                        "Data gagal masuk Google Sheet."
                    )
                        
                waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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

                log(f"✅ Upload selesai ({summary['uploaded']})")

                if summary["uploaded"] > 0 and summary["uploaded"] % 50 == 0:

                    log("♻ Restart Browser")
                
                    client.close()
                
                    client.start()
                
                    client.login()
                
                    downloader = PDFDownloader(
                
                        client.context,
                
                        log
                
                    )
                
                    log("✅ Browser berhasil direstart")

                if progress:

                    persen = summary["total"] / total_orders
                
                    progress.progress(persen)
                
                if status:
                
                    status.info(
                
                        f"Memproses {summary['total']} / {total_orders}"
                
                    )
        
                try:
        
                    if os.path.exists(file_pdf):

                        os.remove(file_pdf)
                    
                        log("🗑 File sementara dihapus")
        
                except Exception:
        
                    pass
        
            except Exception as e:
        
                summary["error"] += 1
        
                log(f"❌ Gagal memproses {order['nomor']}")
        
                log(str(e))
        
                continue

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
