# KAP Finansal Tablo İndirici

## Proje Amacı

[kap.org.tr](https://www.kap.org.tr/tr) üzerindeki **Finansal Tablolar** bölümünden, belirtilen şirketlere ait tüm yıllara ait finansal tabloları otomatik olarak Excel (ZIP) formatında indirmek.

---

## Teknik Gereksinimler

| Alan | Detay |
|------|-------|
| Dil | Python 3.x |
| Ana Paket | `selenium` |
| Tarayıcı | Google Chrome |
| Driver | ChromeDriver (Chrome sürümüyle uyumlu) |

### Bağımlılıklar

```bash
pip install selenium webdriver-manager
```

---

## Proje Yapısı

```
kap_indirici/
│
├── main.py               # Ana çalıştırma dosyası
├── config.py             # Şirket listesi ve ayarlar
├── scraper.py            # Selenium işlemleri
├── utils.py              # Yardımcı fonksiyonlar
└── downloads/            # İndirilen ZIP dosyaları
```

---

## Konfigürasyon (`config.py`)

```python
# Test şirketleri
SIRKET_LISTESI = ["ACSEL", "THYAO"]

# İndirme klasörü (mutlak yol kullan)
import os
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# Sayfa yükleme bekleme süreleri (saniye)
SAYFA_BEKLEME = 5
ELEMENT_BEKLEME = 15
INDIRME_BEKLEME = 20
```

---

## İş Akışı

```
Başla
  │
  ▼
Chrome tarayıcıyı bot-korumasını bypass ederek aç
  │
  ▼
https://www.kap.org.tr/tr adresini aç
  │
  ▼
"Finansal Tablolar" sekmesine tıkla
  │
  ┌─────────────────────────────────────┐
  │  DIŞ LOOP: Şirket Listesi           │
  │  (ACSEL, THYAO, ...)                │
  │                                     │
  │   ┌─────────────────────────────┐   │
  │   │  Şirket adını gir           │   │
  │   │  Açılan öneriyi seç         │   │
  │   │                             │   │
  │   │  İÇ LOOP: Yıllar            │   │
  │   │  (2025, 2024, 2023, ...)    │   │
  │   │                             │   │
  │   │    Yılı ComboBox'tan seç    │   │
  │   │    Periyot: "Tüm Dönemler"  │   │
  │   │    İNDİR butonuna bas       │   │
  │   │    ZIP inişini bekle        │   │
  │   └─────────────────────────────┘   │
  └─────────────────────────────────────┘
  │
  ▼
Bitti
```

---

## Uygulama Detayları

### 1. Chrome Bot Koruması Bypass (`utils.py`)

KAP sitesi Angular tabanlı dinamik bir uygulama olduğundan, Selenium ile açıldığında zaman zaman bot tespiti yapılabilir. Aşağıdaki önlemlerin **tamamı** birlikte uygulanmalıdır:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

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
```

---

### 2. Element Bulucu Yardımcı Fonksiyon

KAP sitesi Angular tabanlı olduğundan element ID'leri dinamik üretilebilir. Aşağıdaki `element_bul` fonksiyonu, birden fazla selector'ı sırayla dener ve ilk bulunanı döner. Hiçbiri bulunamazsa sayfanın HTML'ini `debug_page.html` dosyasına kaydeder:

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
            el = wait.until(EC.presence_of_element_located((by, deger)))
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
```

---

### 3. Ana Scraper Mantığı (`scraper.py`)

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from utils import element_bul

KAP_ANA_URL   = "https://www.kap.org.tr/tr"
FIN_TABLO_URL = "https://www.kap.org.tr/tr/finansal-tablo"

# ── Olası selector listeleri ──────────────────────────────────────────────────
# Her liste için en güvenilir seçenek başa alınmıştır.
# KAP'ın HTML'i değişirse buraya yeni selector'lar eklenebilir.

SIRKET_INPUT_SELECTORS = [
    (By.CSS_SELECTOR, "input[placeholder*='irket']"),
    (By.CSS_SELECTOR, "input[placeholder*='Şirket']"),
    (By.XPATH,        "//input[contains(@placeholder,'irket')]"),
    (By.CSS_SELECTOR, "input.company-search"),
    (By.ID,           "companySearch"),
    (By.ID,           "sirketUnvani"),
]

ONERI_SELECTORS = [
    (By.CSS_SELECTOR, "ul.suggestion-list li:first-child"),
    (By.CSS_SELECTOR, ".autocomplete-items div:first-child"),
    (By.CSS_SELECTOR, ".dropdown-item:first-child"),
    (By.XPATH,        "(//ul[contains(@class,'suggest')]//li)[1]"),
    (By.XPATH,        "(//*[contains(@class,'suggestion')])[1]"),
]

YIL_SELECT_SELECTORS = [
    (By.XPATH, "//select[.//option[string-length(normalize-space())=4 and number(normalize-space())>2000]]"),
    (By.CSS_SELECTOR, "select[name*='yil'], select[id*='yil'], select[id*='Yil']"),
    (By.ID,           "yilSecimi"),
    (By.CSS_SELECTOR, "select.year-select"),
]

PERIYOT_SELECT_SELECTORS = [
    (By.XPATH, "//select[.//option[contains(text(),'Dönem') or contains(text(),'dönem')]]"),
    (By.CSS_SELECTOR, "select[name*='periyot'], select[id*='periyot']"),
    (By.CSS_SELECTOR, "select[name*='period'], select[id*='period']"),
    (By.ID,           "periyotSecimi"),
]

INDIR_BTN_SELECTORS = [
    (By.XPATH, "//button[contains(text(),'ndir')]"),
    (By.XPATH, "//button[contains(text(),'NDIR')]"),
    (By.CSS_SELECTOR, "button.download-btn"),
    (By.CSS_SELECTOR, "button[type='submit']"),
    (By.XPATH, "//a[contains(text(),'ndir')]"),
]

FIN_TAB_MENU_SELECTORS = [
    (By.XPATH, "//a[contains(text(),'Finansal Tablo')]"),
    (By.CSS_SELECTOR, "a[href*='finansal-tablo']"),
    (By.XPATH, "//li//a[contains(text(),'Finansal')]"),
]
# ─────────────────────────────────────────────────────────────────────────────

def finansal_tablolari_indir(driver, sirket_listesi: list, bekleme: int = 15):

    # Ana sayfayı aç
    driver.get(KAP_ANA_URL)
    time.sleep(4)

    # "Finansal Tablolar" menüsüne tıkla, bulamazsa direkt URL ile git
    try:
        fin_tab_link = element_bul(driver, FIN_TAB_MENU_SELECTORS, bekleme=8)
        fin_tab_link.click()
        time.sleep(3)
    except Exception:
        driver.get(FIN_TABLO_URL)
        time.sleep(4)

    for sirket in sirket_listesi:
        print(f"\n>>> Şirket işleniyor: {sirket}")

        try:
            # ── Şirket adını gir ─────────────────────────────────────────────
            sirket_input = element_bul(driver, SIRKET_INPUT_SELECTORS, bekleme)
            sirket_input.clear()
            time.sleep(0.5)
            sirket_input.send_keys(sirket)
            time.sleep(2)  # Autocomplete listesinin yüklenmesini bekle

            # ── Açılan öneriyi seç ───────────────────────────────────────────
            oneri = element_bul(driver, ONERI_SELECTORS, bekleme)
            oneri.click()
            time.sleep(2)

            # ── Yıl ComboBox'ındaki mevcut yılları oku ───────────────────────
            yil_el = element_bul(driver, YIL_SELECT_SELECTORS, bekleme)
            mevcut_yillar = [
                opt.text.strip()
                for opt in Select(yil_el).options
                if opt.text.strip().isdigit() and int(opt.text.strip()) <= 2025
            ]
            print(f"  Bulunan yıllar: {mevcut_yillar}")

            if not mevcut_yillar:
                print(f"  ⚠️  {sirket} için yıl bulunamadı, atlanıyor.")
                continue

            # ── İÇ LOOP: Her yıl için indir ──────────────────────────────────
            for yil in mevcut_yillar:
                print(f"  -> Yıl: {yil}")

                # Yılı seç
                yil_el = element_bul(driver, YIL_SELECT_SELECTORS, bekleme)
                Select(yil_el).select_by_visible_text(yil)
                time.sleep(1)

                # Periyot: Tüm Dönemler
                try:
                    periyot_el = element_bul(driver, PERIYOT_SELECT_SELECTORS, bekleme)
                    periyot_select = Select(periyot_el)
                    for opt in periyot_select.options:
                        if "tüm" in opt.text.lower() or "all" in opt.text.lower():
                            periyot_select.select_by_visible_text(opt.text)
                            break
                    time.sleep(1)
                except Exception as e:
                    print(f"     ⚠️  Periyot seçimi başarısız (devam ediliyor): {e}")

                # İNDİR butonuna bas
                indir_btn = element_bul(driver, INDIR_BTN_SELECTORS, bekleme)
                indir_btn.click()

                # ZIP inişini bekle
                time.sleep(20)
                print(f"     ✅ ZIP indirildi: {sirket} - {yil}")

        except Exception as e:
            print(f"\n  ❌ {sirket} için hata: {e}")
            print("  → Sonraki şirkete geçiliyor...\n")
            continue
```

---

### 4. Ana Çalıştırıcı (`main.py`)

```python
from config import SIRKET_LISTESI, DOWNLOAD_DIR, ELEMENT_BEKLEME
from scraper import finansal_tablolari_indir
from utils import klasor_olustur, tarayici_ac
import time

def main():
    klasor_olustur(DOWNLOAD_DIR)
    driver = tarayici_ac(DOWNLOAD_DIR)

    try:
        finansal_tablolari_indir(driver, SIRKET_LISTESI, ELEMENT_BEKLEME)
        print("\n✅ Tüm işlemler tamamlandı.")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
    finally:
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    main()
```

---

## Hata Ayıklama Rehberi

Kod bir element bulamazsa `debug_page.html` dosyası otomatik oluşturulur. Bu dosyayı tarayıcıda açıp `Ctrl+F` ile aşağıdaki kelimeleri arayarak doğru selector'ı bulabilirsin:

| Aranacak kelime | Hangi element için |
|---|---|
| `placeholder` | Şirket arama kutusu |
| `suggestion`, `autocomplete`, `dropdown` | Şirket öneri listesi |
| `select` + `yil` veya `year` | Yıl ComboBox |
| `select` + `periyot` veya `period` | Dönem ComboBox |
| `İNDİR`, `indir`, `download` | İndirme butonu |

Bulunan gerçek değeri `scraper.py` içindeki ilgili `*_SELECTORS` listesinin **başına** ekle.

---

## Önemli Notlar

### ⏱️ Bekleme Süreleri
Sayfa gecikmelerine karşı `time.sleep()` kullanılmıştır. Yavaş internet bağlantısında `config.py` içindeki `INDIRME_BEKLEME` ve `ELEMENT_BEKLEME` değerleri artırılabilir.

### 🛡️ Bot Koruması
Kodda uygulanan 5 katmanlı bypass stratejisi: `AutomationControlled` bayrağı kapatıldı, otomasyon extension'ı devre dışı bırakıldı, gerçekçi `user-agent` tanımlandı, `navigator.webdriver` CDP ile gizlendi, `navigator.plugins` ve `navigator.languages` gerçekçi değerlerle dolduruldu.

### 📁 İndirme Klasörü
Tüm ZIP dosyaları `downloads/` klasörüne kaydedilir. İndirme yolunun **mutlak yol** (absolute path) olması zorunludur — aksi halde Chrome farklı bir klasöre indirebilir.

---

## Test Şirketleri

| Kısa Ad | Tam Unvan |
|---------|-----------|
| ACSEL | Acıselsan Acıpayam Selüloz Sanayi ve Ticaret A.Ş. |
| THYAO | Türk Hava Yolları A.O. |

---

## Geliştirme Yol Haritası

- [ ] Kodu çalıştır, hata çıkarsa `debug_page.html` ile gerçek selector'ları doğrula
- [ ] İndirilen ZIP dosyalarını `{SIRKET}_{YIL}.zip` formatında yeniden adlandır
- [ ] Hata durumunda otomatik yeniden deneme (retry, max 3) ekle
- [ ] `logging` modülü ile işlem logu dosyaya yaz
- [ ] Büyük şirket listesi için çalıştırmadan önce 2-3 şirketle test et
