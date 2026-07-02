import os
import streamlit as st
from datetime import datetime

from google.oauth2.service_account import Credentials

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import *


class DriveManager:

    def __init__(self, log=print):

        self.log = log
    
        self.folder_cache = {}
    
        self.log("☁ Menghubungkan Google Drive...")
    
        scope = [
            "https://www.googleapis.com/auth/drive"
        ]
    
        creds = Credentials.from_service_account_info(
    
            st.secrets["gcp_service_account"],
    
            scopes=scope
    
        )
    
        self.service = build(
    
            "drive",
    
            "v3",
    
            credentials=creds
    
        )
    
        self.log("✅ Google Drive berhasil terkoneksi")

        # =====================================
        # Service Account (Streamlit Cloud)
        # =====================================
        
        creds = Credentials.from_service_account_info(
        
            st.secrets["gcp_service_account"],
        
            scopes=scope
        
        )
        
        self.log("✅ Service Account berhasil dimuat")

        # =====================================
        # Google Drive API
        # =====================================
        
        self.service = build(
        
            "drive",
        
            "v3",
        
            credentials=creds
        
        )
        
        self.log("✅ Google Drive berhasil terkoneksi")

    # =====================================================
    # PARSE DATE
    # =====================================================

    def parse_date(self, tanggal):

        try:

            return datetime.strptime(
                tanggal,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            return datetime.strptime(
                tanggal,
                "%Y-%m-%d"
            )

    # =====================================================
    # FIND FOLDER
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
            fields="files(id,name)"
        ).execute()

        folders = result.get("files", [])

        if folders:

            return folders[0]["id"]

        return None

    # =====================================================
    # CREATE FOLDER
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

            fields="id"

        ).execute()

        self.log("✅ Folder berhasil dibuat")

        return folder["id"]

    # =====================================================
    # GET FOLDER
    # =====================================================

    def get_folder(self, name, parent):

        cache_key = f"{parent}_{name}"

        if cache_key in self.folder_cache:

            return self.folder_cache[cache_key]

        folder_id = self.find_folder(name, parent)

        if folder_id is None:

            folder_id = self.create_folder(
                name,
                parent
            )

        self.folder_cache[cache_key] = folder_id

        return folder_id

    # =====================================================
    # FIND FILE
    # =====================================================

    def find_file(self, filename, parent):

        query = (
            f"name='{filename}' "
            f"and '{parent}' in parents "
            "and trashed=false"
        )

        result = self.service.files().list(

            q=query,

            fields="files(id,name)"

        ).execute()

        files = result.get("files", [])

        if files:

            return files[0]["id"]

        return None

    # =====================================================
    # UPLOAD
    # =====================================================

    def upload(self, filepath, tanggal):

        self.log("=" * 80)
        self.log("☁ UPLOAD GOOGLE DRIVE")
        self.log("=" * 80)

        dt = self.parse_date(tanggal)

        tahun = dt.strftime("%Y")

        bulan = dt.strftime("%Y-%m")

        self.log(f"📅 Tahun : {tahun}")
        self.log(f"📅 Bulan : {bulan}")

        folder_tahun = self.get_folder(

            tahun,
        
            st.secrets["DRIVE_PARENT_FOLDER_ID"]
        
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

            self.log("⚠ File sudah ada di Google Drive")

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

                fields="id"

            ).execute()

            file_id = file["id"]

            self.log("✅ Upload berhasil")

        link = f"https://drive.google.com/file/d/{file_id}/view"

        self.log(f"🔗 {link}")

        return link
