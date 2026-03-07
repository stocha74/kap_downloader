from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os


def klasor_olustur(path: str):
    os.makedirs(path, exist_ok=True)


def tarayici_ac(download_dir: str) -> webdriver.Chrome:
    options = Options()

    # 1) Otomasyon bayrağını kaldır
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # 2) Gerçek kullanıcı gibi görünmek için user-agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # 3) Ek kararlılık argümanları
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    # 4) İndirme klasörü — mutlak yol zorunlu
    abs_download_dir = os.path.abspath(download_dir)
    prefs = {
        "download.default_directory": abs_download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)

    # 5) navigator.webdriver özelliğini CDP ile gizle
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr']});
            """
        }
    )

    return driver


def element_bul(driver, selector_listesi: list, bekleme: int = 15):
    """
    selector_listesi: [(By.ID, "deger"), (By.CSS_SELECTOR, ".sinif"), ...]
    formatında olası selector'ların listesi.
    İlk bulunanı döner, hiçbiri bulunamazsa debug_page.html kaydeder ve hata fırlatır.
    """
    hatalar = []
    for by, deger in selector_listesi:
        try:
            wait = WebDriverWait(driver, min(bekleme, 5))
            el = wait.until(EC.element_to_be_clickable((by, deger)))
            return el
        except Exception as e:
            hatalar.append(f"  [{by}='{deger}']")

    # Hiçbiri bulunamadıysa sayfanın HTML'ini kaydet
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    raise Exception(
        "Element bulunamadı! Denenen selector'lar:\n" + "\n".join(hatalar) +
        "\n\n→ debug_page.html dosyası oluşturuldu. "
        "Bu dosyayı tarayıcıda açıp aşağıdaki 'Hata Ayıklama' bölümündeki "
        "kelimeleri arayarak doğru selector'ı bulabilirsin."
    )
