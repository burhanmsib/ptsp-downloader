import logging
import os


class Logger:

    def __init__(self, callback=None):

        self.callback = callback

        os.makedirs(
            "logs",
            exist_ok=True
        )

        self.logger = logging.getLogger("PTSP")

        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:

            formatter = logging.Formatter(

                "%(asctime)s | %(levelname)s | %(message)s"

            )

            info_handler = logging.FileHandler(
                "logs/downloader.log",
                encoding="utf-8"
            )

            info_handler.setFormatter(formatter)

            self.logger.addHandler(info_handler)

    # =====================================================

    def _show(self, icon, text):

        pesan = f"{icon} {text}"

        print(pesan)

        self.logger.info(text)

        if self.callback:

            self.callback(pesan)

    # =====================================================

    def info(self, text):

        self._show("ℹ️", text)

    # =====================================================

    def success(self, text):

        self._show("✅", text)

    # =====================================================

    def warning(self, text):

        self._show("⚠️", text)

    # =====================================================

    def error(self, text):

        print(f"❌ {text}")

        self.logger.error(text)

        if self.callback:

            self.callback(f"❌ {text}")