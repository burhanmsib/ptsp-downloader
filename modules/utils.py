from pathlib import Path


# =====================================================
# MEMBUAT FOLDER
# =====================================================

def ensure_folder(folder, log=print):

    folder = Path(folder)

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    log(f"📁 Folder siap : {folder}")

    return folder

# =====================================================
# EKSTENSI FILE DARI URL
# =====================================================

def file_extension(url):

    """Ambil ekstensi file dari URL, mis. 'pdf', 'rar'. Kosong jika tidak ada."""

    from urllib.parse import urlparse, unquote

    name = unquote(urlparse(url or "").path).rsplit("/", 1)[-1]

    if "." not in name:

        return ""

    return name.rsplit(".", 1)[-1].lower()
