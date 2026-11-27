import os
import requests

from modules.utils import file_extension


class PDFDownloader:

    def __init__(self, context, log=print):

        self.context = context
        self.log = log

    # =====================================================
    # DOWNLOAD PDF
    # =====================================================

    def download(self, order, pdf_url):

        self.log("=" * 80)
        self.log("⬇️ DOWNLOAD DOKUMEN")
        self.log("=" * 80)

        cookies = self.context.cookies()

        session = requests.Session()

        # ==========================================
        # Salin cookie Playwright ke Requests
        # ==========================================

        for cookie in cookies:

            session.cookies.set(
                cookie["name"],
                cookie["value"]
            )

        self.log("🌐 Mengunduh dokumen...")

        response = session.get(pdf_url)

        if response.status_code != 200:

            self.log(f"❌ Download gagal ({response.status_code})")

            return None

        # Jika server mengembalikan halaman HTML (mis. sesi habis),
        # anggap gagal agar tidak mengupload file yang salah.
        if "text/html" in response.headers.get("Content-Type", "").lower():

            self.log("❌ Server mengembalikan halaman HTML, bukan file")

            return None

        if not response.content:

            self.log("❌ File kosong")

            return None

        os.makedirs(
            "downloads/temp",
            exist_ok=True
        )

        filename = (
            order["nomor"]
            .replace("/", "_")
            + "." + (file_extension(pdf_url) or "pdf")
        )

        filepath = os.path.join(
            "downloads/temp",
            filename
        )

        with open(filepath, "wb") as f:

            f.write(response.content)

        self.log("✅ Download selesai")

        self.log(f"📄 Nama File : {filename}")

        self.log(f"📂 Lokasi : {filepath}")

        return filepath