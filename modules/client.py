from playwright.sync_api import sync_playwright
from config import *
import re


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

                    id: row.querySelector(".selectedrow").value,

                    nomor: td[1].innerText.trim(),

                    layanan: td[2].innerText.trim(),

                    tanggal_permohonan: td[3].innerText.trim(),

                    tanggal_jatuh_tempo: td[4].innerText.trim(),

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
    
        page = 1
    
        while True:
    
            self.log("")
            self.log("=" * 80)
            self.log(f"Mengambil daftar order halaman {page}")
            self.log("=" * 80)
    
            orders = self.get_orders()
    
            self.log(f"📄 Ditemukan {len(orders)} order")
    
            # all_orders.extend(orders)

            for order in orders:

                if order["nomor"] not in [o["nomor"] for o in all_orders]:
            
                    all_orders.append(order)
                    self.log(
                        f"Total sementara : {len(all_orders)}"
                    )
    
            if not self.goto_next_page():
    
                break
    
            page += 1
    
        self.log("")
        self.log("=" * 80)
        self.log(f"TOTAL ORDER TERKUMPUL : {len(all_orders)}")
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

        self.log("=" * 80)
        self.log("Mengecek halaman detail...")
        self.log("=" * 80)

        html = self.page.content()

        # Cari langsung link upload/dokumen/*.pdf
        hasil = re.search(
            r'https://ptsp\.bmkg\.go\.id/upload/dokumen/[^\s"]+\.pdf',
            html
        )

        if hasil:

            pdf_url = hasil.group(0)

            self.log("✅ PDF ditemukan")
            self.log(pdf_url)

            return {
                "status": "READY",
                "pdf_url": pdf_url
            }

        self.log("⌛ Belum ada file PDF")

        return {
            "status": "WAITING",
            "pdf_url": None
        }
    
    def search_month(self, bulan):
    
        self.log(f"📅 Mencari order bulan {bulan}")
    
        search = self.page.locator('input[type="search"]')
    
        search.wait_for()
    
        search.fill("")
    
        search.fill(bulan)
    
        self.page.wait_for_timeout(3000)

    # def get_total_pages(self):

    #     self.page.wait_for_selector("ul.pagination")
    
    #     pages = self.page.locator("ul.pagination li")
    
    #     total = pages.count()
    
    #     # Previous + angka + Next
    #     if total <= 2:
    #         total_page = 1
    #     else:
    #         total_page = total - 2
    
    #     self.log(f"📄 Total halaman : {total_page}")
    
    #     return total_page
    
    # def goto_page(self, page):

    #     if page == 0:
    
    #         self.log("📄 Halaman pertama")
    
    #         return
    
    #     self.page.locator("ul.pagination li").nth(page + 1).click()
    
    #     self.page.wait_for_timeout(3000)
    
    #     self.log(f"📄 Pindah ke halaman {page+1}")

      def goto_next_page(self):
    
        next_btn = self.page.locator(
            "button[aria-label='Next'], li.next, li.paginate_button.next"
        )
    
        if next_btn.count() == 0:
    
            return False
    
        try:
    
            disabled = (
                next_btn.first.get_attribute("disabled")
            )
    
            cls = next_btn.first.get_attribute("class") or ""
    
            if disabled is not None:
    
                return False
    
            if "disabled" in cls:
    
                return False
    
            next_btn.first.click()
    
            self.page.wait_for_load_state("networkidle")
    
            self.page.wait_for_timeout(2000)
    
            return True
    
        except Exception:
    
            return False
