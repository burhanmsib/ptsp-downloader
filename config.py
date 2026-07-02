import os

# =====================================================
# PTSP
# =====================================================

BASE_URL = "https://ptsp.bmkg.go.id"

LOGIN_URL = f"{BASE_URL}/backend/login"

ORDER_URL = f"{BASE_URL}/backend/katalog_pelayanan/order_terbayar"


# =====================================================
# PLAYWRIGHT
# =====================================================

HEADLESS = True

SLOW_MO = 0


# =====================================================
# FOLDER
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_TEMP = os.path.join(
    BASE_DIR,
    "downloads",
    "temp"
)

DOWNLOAD_FINISHED = os.path.join(
    BASE_DIR,
    "downloads",
    "finished"
)

CACHE_FOLDER = os.path.join(
    BASE_DIR,
    "cache"
)

LOG_FOLDER = os.path.join(
    BASE_DIR,
    "logs"
)

STORAGE_STATE = os.path.join(
    CACHE_FOLDER,
    "storage_state.json"
)


# =====================================================
# GOOGLE SHEET
# =====================================================

SHEET_NAME = "Sheet1"
SHEET_ID = "1eU06_6SDulmSYu_IISGtDqCN3fa00fX-_O3p4jNDo38"


# =====================================================
# GOOGLE DRIVE
# =====================================================

DRIVE_PARENT_FOLDER_ID = "1HnVL9SlEl8LWWtHGIwytmWam05TkVZKR"
