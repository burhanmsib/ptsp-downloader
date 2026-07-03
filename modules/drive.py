import os
from datetime import datetime

import streamlit as st

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class DriveManager:

    def __init__(self, log=print):

        self.log = log
        self.folder_cache = {}

        self.log("☁ Menghubungkan Google Drive...")

        scope = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
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

        self.service = build(

            "drive",

            "v3",

            credentials=self.creds,

            cache_discovery=False

        )

        self.log("✅ Google Drive berhasil terkoneksi")

    # =====================================================

    def parse_date(self, tanggal):

        try:

            return datetime.strptime(
                tanggal,
                "%Y-%m-%d %H:%M:%S"
            )

        except:

            return datetime.strptime(
                tanggal,
                "%Y-%m-%d"
            )

    # =====================================================

    def find_folder(self, name, parent):

        query = (

            "mimeType='application/vnd.google-apps.folder' "

            f"and name='{name}' "

            f"and '{parent}' in parents "

            "and trashed=false"

        )

        result = self.service.files().list(

            q=query,

            fields="files(id,name)",

            supportsAllDrives=True,

            includeItemsFromAllDrives=True

        ).execute()

        folders = result.get("files", [])

        if folders:

            return folders[0]["id"]

        return None

    # =====================================================

    def create_folder(self, name, parent):

        self.log(f"📁 Membuat folder {name}")

        metadata = {

            "name": name,

            "mimeType": "application/vnd.google-apps.folder",

            "parents": [parent]

        }

        folder = self.service.files().create(

            body=metadata,

            fields="id",

            supportsAllDrives=True

        ).execute()

        self.log("✅ Folder berhasil dibuat")

        return folder["id"]

    # =====================================================

    def get_folder(self, name, parent):

        key = f"{parent}_{name}"

        if key in self.folder_cache:

            return self.folder_cache[key]

        folder = self.find_folder(name, parent)

        if folder is None:

            folder = self.create_folder(name, parent)

        self.folder_cache[key] = folder

        return folder

    # =====================================================

    def find_file(self, filename, parent):

        query = (

            f"name='{filename}' "

            f"and '{parent}' in parents "

            "and trashed=false"

        )

        result = self.service.files().list(

            q=query,

            fields="files(id,name)",

            supportsAllDrives=True,

            includeItemsFromAllDrives=True

        ).execute()

        files = result.get("files", [])

        if files:

            return files[0]["id"]

        return None

    # =====================================================

    def upload(self, filepath, tanggal):

        self.log("=" * 80)

        self.log("☁ UPLOAD GOOGLE DRIVE")

        self.log("=" * 80)

        dt = self.parse_date(tanggal)

        tahun = dt.strftime("%Y")

        bulan = dt.strftime("%Y-%m")

        parent = st.secrets["google"]["drive_parent"]

        folder_tahun = self.get_folder(

            tahun,

            parent

        )

        folder_bulan = self.get_folder(

            bulan,

            folder_tahun

        )

        filename = os.path.basename(filepath)

        self.log(f"📄 File : {filename}")

        file_id = self.find_file(

            filename,

            folder_bulan

        )

        if file_id:

            self.log("⚠ File sudah ada")

        else:

            media = MediaFileUpload(

                filepath,

                mimetype="application/pdf",

                resumable=False

            )

            metadata = {

                "name": filename,

                "parents": [folder_bulan]

            }

            file = self.service.files().create(

                body=metadata,

                media_body=media,

                fields="id",

                supportsAllDrives=True

            ).execute()

            file_id = file["id"]

            self.log("✅ Upload berhasil")

        return f"https://drive.google.com/file/d/{file_id}/view"
