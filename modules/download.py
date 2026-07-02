import os
import requests


class PDFDownloader:

    def __init__(self, context, log=print):

        self.context = context
        self.log = log

    # =====================================================
    # DOWNLOAD PDF
    # =====================================================

    def download(self, order, pdf_url):

        self.log("=" * 80)
        self.log("⬇️ DOWNLOAD PDF")
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

        self.log("🌐 Mengunduh PDF...")

        response = session.get(pdf_url)

        if response.status_code != 200:

            self.log(f"❌ Download gagal ({response.status_code})")

            return None

        os.makedirs(
            "downloads/temp",
            exist_ok=True
        )

        filename = (
            order["nomor"]
            .replace("/", "_")
            + ".pdf"
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