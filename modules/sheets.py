import gspread
import streamlit as st

from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


class SheetManager:

    def __init__(self, log=print):

        self.log = log

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        oauth = st.secrets["oauth"]

        self.creds = Credentials(

            token=oauth["token"],

            refresh_token=oauth["refresh_token"],

            token_uri=oauth["token_uri"],

            client_id=oauth["client_id"],

            client_secret=oauth["client_secret"],

            scopes=scope

        )

        if not self.creds.valid:

            self.log("🔄 Refresh OAuth Token...")

            self.creds.refresh(Request())

            self.log("✅ Token berhasil diperbarui")

        client = gspread.authorize(self.creds)

        self.sheet = client.open_by_key(

            st.secrets["google"]["sheet_id"]

        ).worksheet(

            st.secrets["google"]["sheet_name"]

        )

        self.log("📊 Google Sheet berhasil terkoneksi")

        self.refresh_cache()

    # =====================================================

    def refresh_cache(self):

        self.log("🔄 Memuat cache Google Sheet...")

        values = self.sheet.get_all_values()

        self.cache = {}

        for index, row in enumerate(values[1:], start=2):

            if not row:
                continue

            nomor = row[0].strip()

            if nomor:
                self.cache[nomor] = index

        self.log(f"✅ Cache berhasil dimuat ({len(self.cache)} data)")

    # =====================================================

    def find_order(self, nomor):

        return self.cache.get(nomor)

    # =====================================================

    def insert(self, order, status):

        self.log("=" * 80)
        self.log("📝 Menambahkan data ke Google Sheet")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [

            order["nomor"],

            order["tanggal_permohonan"],

            order["perusahaan"],

            "",

            status,

            now,

            "",

            "",

            now

        ]

        self.sheet.append_row(row)

        self.cache[order["nomor"]] = len(

            self.sheet.get_all_values()

        )

        self.log("✅ Data berhasil ditambahkan")

    # =====================================================

    def update(self, row, **kwargs):

        self.log("✏ Memperbarui Google Sheet")

        data = self.sheet.row_values(row)

        while len(data) < 9:
            data.append("")

        if "nama_file" in kwargs:
            data[3] = kwargs["nama_file"]

        if "status" in kwargs:
            data[4] = kwargs["status"]

        if "waktu_download" in kwargs:
            data[5] = kwargs["waktu_download"]

        if "google_drive" in kwargs:
            data[6] = kwargs["google_drive"]

        if "pdf_url" in kwargs:
            data[7] = kwargs["pdf_url"]

        if "last_check" in kwargs:
            data[8] = kwargs["last_check"]

        self.sheet.update(

            f"A{row}:I{row}",

            [data]

        )

        self.log("✅ Google Sheet berhasil diperbarui")
