from datetime import datetime
import os
import time

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
        "error": 0,
        "bulan": bulan,
        "waiting_list": [],
        "error_list": []
    }

    start_time = time.time()

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
        log("✅ Google Sheet terkoneksi")

        drive = DriveManager(

            log
        
        )

        log("✅ Google Drive terkoneksi")

        log(f"📅 Bulan pencarian : {bulan}")

        log("📋 Mengumpulkan seluruh order...")
        
        orders = client.collect_all_orders(bulan)
        total_orders = len(orders)

        if total_orders == 0:

            log(f"⚠ Tidak ada order dengan Tanggal Pembayaran {bulan}.")
        
            return summary
        
        log(f"📄 Total order ditemukan : {len(orders)}")

        def update_progress():

            if progress and total_orders > 0:

                progress.progress(min(summary["total"] / total_orders, 1.0))

            if status:

                persen = (summary["total"] / total_orders) * 100

                status.markdown(
                    f"""
### 📦 Backup PTSP BMKG — {bulan}

**Progress : {summary['total']} / {total_orders} ({persen:.1f}%)**

| Status | Jumlah |
|--------|-------:|
| ✅ Uploaded | **{summary['uploaded']}** |
| ⌛ Waiting | **{summary['waiting']}** |
| ⏭ Sudah ada | **{summary['skip']}** |
| ❌ Error | **{summary['error']}** |
"""
                )

        for order in orders:

            try:
        
                summary["total"] += 1
        
                log("-" * 60)
                log(f"Nomor : {order['nomor']}")
        
                log(f"Tanggal Pembayaran : {order['tanggal_pembayaran']}")

                row = sheet.find_order(order["nomor"])

                status_lama = sheet.get_status(order["nomor"])

                if row is not None and status_lama == "WAITING":

                    # PDF mungkin sudah tersedia sekarang
                    log("🔁 Status sebelumnya WAITING, cek ulang PDF")

                elif row is not None:

                    # Sudah pernah diupload: lewati hanya jika file-nya
                    # masih ada di Google Drive (tidak dihapus/di Trash).
                    if drive.file_exists(
                        sheet.get_drive_link(order["nomor"]),
                        bulan
                    ):

                        summary["skip"] += 1

                        log("⏭ Sudah ada di Google Drive")

                        continue

                    log(f"♻ File tidak ditemukan di folder Drive {bulan}, download ulang")
        
                log(f"🌐 Membuka {order['detail']}")
                
                client.open_detail(order)
        
                hasil = client.get_pdf_url()
        
                if hasil["status"] == "WAITING":

                    if row is None:

                        sheet.insert(
                            order,
                            "WAITING"
                        )

                    else:

                        sheet.update(
                            row,
                            last_check=datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                        )
                
                    summary["waiting"] += 1

                    summary["waiting_list"].append({
                        "No Permohonan": order["nomor"],
                        "Tanggal Pembayaran": order["tanggal_pembayaran"],
                        "Pemohon": order["pemohon"],
                        "Perusahaan": order["perusahaan"]
                    })
                
                    log("⌛ PDF belum tersedia")
                
                    continue
                
                if not hasil["pdf_url"]:
                
                    raise Exception("PDF URL kosong.")
        
                log("⬇ Download PDF...")

                file_pdf = None
                
                for retry in range(3):
                
                    try:
                
                        file_pdf = downloader.download(
                            order,
                            hasil["pdf_url"]
                        )
                        
                        if file_pdf and os.path.exists(file_pdf):
                            break
                
                    except Exception as e:
                
                        log(f"⚠ Retry Download {retry+1}/3")
                
                        log(str(e))
                
                        time.sleep(2)
                
                if file_pdf is None:
                
                    raise Exception("Download PDF gagal.")
        
                log("☁ Upload Google Drive...")

                drive_link = None

                for retry in range(3):
                
                    try:
                
                        drive_link = drive.upload(
                            file_pdf,
                            # Folder Drive mengikuti bulan Tanggal Pembayaran
                            order["tanggal_pembayaran"]
                        )
                
                        break
                
                    except Exception as e:
                
                        log(f"⚠ Retry Upload {retry+1}/3")
                
                        log(str(e))
                
                        time.sleep(2)
                
                if drive_link is None:
                
                    raise Exception("Upload Google Drive gagal.")
        
                if row is None:

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
        
                for retry in range(3):

                    try:
                
                        sheet.update(
                            row,
                            nama_file=os.path.basename(file_pdf),
                            status="UPLOADED",
                            google_drive=drive_link,
                            pdf_url=hasil["pdf_url"],
                            waktu_download=waktu,
                            last_check=waktu
                        )
                
                        break
                
                    except Exception as e:
                
                        log(f"⚠ Retry Google Sheet {retry+1}/3")
                
                        log(str(e))
                
                        time.sleep(2)
                
                        if retry == 2:
                
                            raise
        
                summary["uploaded"] += 1

                log(f"✅ Upload selesai ({summary['uploaded']})")

                if summary["uploaded"] > 0 and summary["uploaded"] % 50 == 0:

                    log("♻ Restart Browser")
                
                    client.close()
                
                    client.start()
                
                    client.login()

                    client.open_orders()
                
                    downloader = PDFDownloader(
                
                        client.context,
                
                        log
                
                    )
                
                    log("✅ Browser berhasil direstart")

                try:

                    if file_pdf and os.path.exists(file_pdf):
                
                        os.remove(file_pdf)
                
                        log("🗑 File sementara dihapus")
                
                except Exception:
                
                    pass
        
            except Exception as e:
        
                summary["error"] += 1

                summary["error_list"].append({
                    "No Permohonan": order["nomor"],
                    "Tanggal Pembayaran": order.get("tanggal_pembayaran", ""),
                    "Error": str(e)
                })
        
                log(f"❌ Gagal memproses {order['nomor']}")
        
                log(str(e))

            finally:

                update_progress()

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
        elapsed = int(time.time() - start_time)

        jam = elapsed // 3600
        
        menit = (elapsed % 3600) // 60
        
        detik = elapsed % 60
        
        log(f"Durasi     : {jam:02d}:{menit:02d}:{detik:02d}")
    
        if summary["error"] == 0:
    
            log("")
            log("🎉 Backup selesai tanpa error")
    
        else:
    
            log("")
            log("⚠ Backup selesai dengan beberapa error")

    return summary
