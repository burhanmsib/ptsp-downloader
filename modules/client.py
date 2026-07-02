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
            headless=HEADLESS,
            slow_mo=SLOW_MO
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

                    detail: row.querySelector('td:last-child a').href

                };

            });

        }
        """)

        self.log(
            f"📄 Jumlah order ditemukan : {len(orders)}"
        )

        return orders
    
    def open_detail(self, order):

        self.log("=" * 80)

        self.log("Membuka Detail")

        self.log("Nomor :", order["nomor"])

        self.log("URL    :", order["detail"])

        self.page.goto(order["detail"])

        self.page.wait_for_load_state("networkidle")

        self.page.wait_for_timeout(3000)

        self.log()

        self.log("Judul :", self.page.title())

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
            r'https://ptsp\.bmkg\.go\.id/upload/dokumen/[^"]+\.pdf',
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

        self.log(
            f"📅 Mencari order bulan {bulan}"
        )
        self.page.evaluate(f"""
        () => {{
            let table = $('#datatable').DataTable();

            table.search('{bulan}');
            table.page.len(100).draw();
        }}
        """)

        self.page.wait_for_timeout(3000)

    def get_total_pages(self):

        info = self.page.evaluate("""
        () => $('#datatable').DataTable().page.info()
        """)

        self.log(info)

        return info["pages"]
    
    def goto_page(self, page):

        self.page.evaluate(f"""
        () => {{
            $('#datatable').DataTable().page({page}).draw(false);
        }}
        """)

        self.page.wait_for_timeout(2000)
        self.log(f"📄 Pindah ke halaman {page+1}")
