from playwright.sync_api import sync_playwright
from datetime import datetime
from config import *
import re
from modules.utils import file_extension


class PTSPClient:

    def __init__(

        self,

        username,

        password,

        log=print

    ):

        self.username = username

        self.password = password

        self.log = log

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        self.context = self.browser.new_context(
            accept_downloads=True
        )

        self.page = self.context.new_page()
        
        self.context.set_default_timeout(60000)

        self.log("🚀 Browser berhasil dijalankan")

    def close(self):

        if self.browser:
    
            self.browser.close()
    
        if self.playwright:
    
            self.playwright.stop()
    
        self.log("🔒 Browser ditutup")
        
    def login(self):

        self.page.goto(LOGIN_URL)

        self.page.fill(
            'input[name="txt_username"]',
            self.username
        )

        self.page.fill(
            'input[name="txt_password"]',
            self.password
        )

        self.page.click(
            'button[type="submit"]'
        )

        self.page.wait_for_load_state("networkidle")

        if "login" in self.page.url.lower():

            raise Exception(
                "Username atau Password PTSP salah."
            )
        
        self.log("✅ Login berhasil")

    def open_orders(self):

        self.page.goto(ORDER_URL)

        self.page.wait_for_load_state("networkidle")

        # Tunggu tabel muncul
        self.page.wait_for_selector("#datatable")
        # self.page.wait_for_function("""
        # () => {
        #     return (
        #         typeof $ !== "undefined" &&
        #         $.fn &&
        #         $.fn.DataTable
        #     );
        # }
        # """)

        self.page.wait_for_selector("#datatable tbody tr")

        self.page.wait_for_timeout(2000)

        self.log("✅ Halaman Order Terbayar terbuka")

        self.log(self.page.url)

        self.page.wait_for_timeout(5000)

    def save_session(self):

        self.context.storage_state(
            path=STORAGE_STATE
        )

        self.log("💾 Session berhasil disimpan")
    
    def get_orders(self):

        self.page.wait_for_function("""
        () => document.querySelectorAll("#datatable tbody tr").length > 0
        """)

        orders = self.page.evaluate("""
        () => {

            return Array.from(
                document.querySelectorAll("#datatable tbody tr")
            ).map(row => {

                const td = row.querySelectorAll("td");

                return {

                    id: row.querySelector(".selectedrow")?.value ?? "",

                    nomor: td[1].innerText.trim(),

                    layanan: td[2].innerText.trim(),

                    tanggal_permohonan: td[3].innerText.replace(/\\s+/g, " ").trim(),

                    // Kolom ke-5 di tabel adalah "Tanggal Pembayaran"
                    tanggal_pembayaran: td[4].innerText.replace(/\\s+/g, " ").trim(),

                    pemohon: td[5].innerText.trim(),

                    perusahaan: td[6].innerText.trim(),

                    hp: td[7].innerText.trim(),

                    detail: row.querySelector("a")?.href ?? ""

                };

            });

        }
        """)

        orders = [o for o in orders if o["detail"]]

        self.log(
            f"📄 Jumlah order ditemukan : {len(orders)}"
        )

        return orders

    def collect_all_orders(self, bulan):
    
        self.search_month(bulan)
    
        all_orders = []
        seen = set()
        dilewati = 0
    
        current_page = 1
    
        while True:
    
            self.log("")
            self.log("=" * 80)
            self.log(f"📄 Mengambil halaman {current_page}")
            self.log("=" * 80)
    
            self.page.wait_for_selector("#datatable tbody tr")
    
            orders = self.get_orders()

            cocok = 0

            for order in orders:

                nomor = order["nomor"]

                if nomor in seen:
                    continue

                seen.add(nomor)

                # Validasi per baris: hanya order yang bulan
                # Tanggal Pembayaran-nya sama dengan bulan yang dipilih
                if order.get("tanggal_pembayaran", "")[:7] != bulan:
                    dilewati += 1
                    continue

                cocok += 1
                all_orders.append(order)

            self.log(
                f"📑 {cocok} order dibayar {bulan} "
                f"(dari {len(orders)} baris di halaman ini)"
            )

            # -----------------------------
            # Cari halaman berikutnya
            # -----------------------------
            next_page = current_page + 1
    
            next_locator = self.page.locator(
                f"ul.pagination a.page-link[data-dt-idx='{next_page-1}']"
            )
    
            if next_locator.count() == 0:
    
                self.log("✅ Sudah halaman terakhir")
    
                break
    
            try:
    
                self.log(f"➡ Pindah ke halaman {next_page}")
    
                next_locator.first.click()
    
                self.page.wait_for_load_state("networkidle")
    
                self.page.wait_for_timeout(3000)
    
                current_page += 1
    
            except Exception as e:
    
                self.log(f"❌ Gagal pindah halaman : {e}")
    
                break
    
        if dilewati:
            self.log(
                f"🚫 {dilewati} order dilewati karena Tanggal Pembayaran "
                f"bukan bulan {bulan}"
            )

        self.log("")
        self.log("=" * 80)
        self.log(f"ORDER DENGAN TANGGAL PEMBAYARAN {bulan} : {len(all_orders)}")
        self.log("=" * 80)

        return all_orders

    def open_detail(self, order):

        self.log("=" * 80)

        self.log("Membuka Detail")

        self.log(f"Nomor : {order['nomor']}")

        self.log(f"URL : {order['detail']}")

        self.page.goto(order["detail"])

        self.page.wait_for_load_state("networkidle")

        self.page.wait_for_selector("body")

        self.page.wait_for_timeout(1000)

        self.log()

        self.log(f"Judul : {self.page.title()}")

        self.log("URL setelah dibuka :")

        self.log(self.page.url)

        self.log()

        self.log("Detail berhasil dibuka")

    def get_pdf_url(self):

        """
        Cari link dokumen hasil (tombol "Dokumen" di kolom Download Data).
        Semua jenis file diterima (pdf, rar, zip, docx, dll).
        Status WAITING hanya jika belum ada dokumen sama sekali.
        """

        self.log("=" * 80)
        self.log("Mengecek halaman detail...")
        self.log("=" * 80)

        # Link dari atribut href (bisa relatif), diubah jadi URL absolut
        # Utamakan link di tabel DATA PRODUK (kolom "Download Data"),
        # supaya tidak tertukar dengan "Dokumen Permohonan".
        links = self.page.evaluate("""
        () => {
            const ambil = (root) => Array.from(root.querySelectorAll("a[href]"))
                .map(a => a.href)
                .filter(h => h.includes("/upload/dokumen/"));

            const th = Array.from(document.querySelectorAll("th, td"))
                .find(el => el.innerText.trim().toLowerCase() === "download data");

            const tabel = th ? th.closest("table") : null;

            if (tabel) {
                return {tabel: true, links: ambil(tabel)};
            }

            return {tabel: false, links: ambil(document)};
        }
        """)

        ada_tabel = links["tabel"]

        links = links["links"]

        if not links and not ada_tabel:

            # Cadangan: cari di HTML mentah
            links = re.findall(
                r'https?://ptsp\.bmkg\.go\.id/upload/dokumen/[^\s"\'<>]+',
                self.page.content()
            )

        links = [
            l for l in links
            if re.search(r"/upload/dokumen/[^/?#]+\.[A-Za-z0-9]{2,5}($|[?#])", l)
        ]

        if links:

            pdf_url = links[0]

            ext = file_extension(pdf_url)

            self.log(f"✅ Dokumen ditemukan ({ext.upper() or '?'})")
            self.log(pdf_url)

            return {
                "status": "READY",
                "pdf_url": pdf_url,
                "ext": ext
            }

        self.log("⌛ Belum ada dokumen")

        return {
            "status": "WAITING",
            "pdf_url": None,
            "ext": ""
        }

    def search_month(self, bulan):

        self.log(f"📅 Mencari order bulan {bulan}")

        # Validasi format YYYY-MM
        try:
            datetime.strptime(bulan, "%Y-%m")
        except ValueError:
            raise ValueError(
                "Format bulan harus YYYY-MM, contoh: 2026-09"
            )

        # Pakai kotak "Search" bawaan tabel (sama seperti mengetik
        # manual di website). Ini mempersempit hasil ke baris yang
        # mengandung bulan tsb; penyaringan akhir berdasarkan
        # Tanggal Pembayaran tetap dilakukan per baris di
        # collect_all_orders.
        try:

            self.page.evaluate(
                """
                (bulan) => {
                    const table = $('#datatable').DataTable();
                    table.columns().search('');
                    table.search(bulan);
                    table.page.len(100).draw();
                }
                """,
                bulan
            )

        except Exception as e:

            self.log(f"⚠ Filter lewat DataTable gagal ({e}), pakai kotak Search")

            search = self.page.locator("input[type='search']").first

            search.fill(bulan)

            search.press("Enter")

            try:
                self.page.select_option(
                    "select[id^='dt-length-'], select[name$='_length']",
                    "100"
                )
            except Exception:
                pass

        self.page.wait_for_load_state("networkidle")

        self.page.wait_for_timeout(3000)

        self.log(f"✅ Pencarian {bulan} diterapkan")
