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