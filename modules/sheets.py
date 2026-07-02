import gspread

from google.oauth2.service_account import Credentials

from datetime import datetime

from config import *

import streamlit as st


class SheetManager:

    def __init__(self, log=print):

        self.log = log

        scope = [

            "https://www.googleapis.com/auth/spreadsheets",

            "https://www.googleapis.com/auth/drive"

        ]

        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )

        client = gspread.authorize(creds)

        self.sheet = client.open_by_key(

            st.secrets["SHEET_ID"]
        
        ).worksheet(
        
            st.secrets["SHEET_NAME"]
        
        )
        self.log("📊 Google Sheet berhasil terkoneksi")

        # =====================================
        # Cache seluruh data
        # =====================================

        self.refresh_cache()

    # =====================================================
    # REFRESH CACHE
    # =====================================================

    def refresh_cache(self):

        self.log("🔄 Memuat cache Google Sheet...")

        values = self.sheet.get_all_values()

        self.cache = {}

        for index, row in enumerate(

            values[1:],

            start=2

        ):

            if len(row) == 0:

                continue

            nomor = row[0].strip()

            if nomor:

                self.cache[nomor] = index

        self.log(f"✅ Cache berhasil dimuat ({len(self.cache)} data)")

    # =====================================================
    # FIND ORDER
    # =====================================================

    def find_order(self, nomor):

        return self.cache.get(nomor)

    # =====================================================
    # INSERT
    # =====================================================

    def insert(self, order, status):

        self.log("=" * 80)
        self.log("📝 Menambahkan data ke Google Sheet")

        row = [

            order["nomor"],

            order["tanggal_permohonan"],

            order["perusahaan"],

            "",

            status,

            datetime.now().strftime(

                "%Y-%m-%d %H:%M:%S"

            ),

            "",

            "",

            datetime.now().strftime(

                "%Y-%m-%d %H:%M:%S"

            )

        ]

        self.sheet.append_row(row)

        self.cache[order["nomor"]] = len(

            self.sheet.get_all_values()

        )

        self.log("✅ Data berhasil ditambahkan")

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self, row, **kwargs):

        self.log("✏️ Memperbarui data Google Sheet")

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
