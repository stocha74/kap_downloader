from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
from utils import element_bul

KAP_ANA_URL = "https://www.kap.org.tr/tr"

# ── Olası selector listeleri ──────────────────────────────────────────────────
# Her liste için en güvenilir seçenek başa alınmıştır.
# KAP'ın HTML'i değişirse buraya yeni selector'lar eklenebilir.

SIRKET_INPUT_SELECTORS = [
    (By.ID,           "search-input"),
    (By.XPATH,        "/html/body/main/section[1]/div/div/div[2]/div[2]/div/div/div[1]/div/div[1]/input"),
    (By.CSS_SELECTOR, "input[placeholder='Şirket Ünvanı']"),
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
    (By.XPATH, "//*[contains(text(),'Finansal Tablolar') and (self::button or self::span or self::div or self::a or self::li)]"),
    (By.XPATH, "//*[contains(text(),'Finansal Tablo')]"),
    (By.CSS_SELECTOR, "a[href*='finansal-tablo']"),
]
# ─────────────────────────────────────────────────────────────────────────────

def finansal_tablolari_indir(driver, sirket_listesi: list, bekleme: int = 15):

    # Ana sayfayı aç
    driver.get(KAP_ANA_URL)
    time.sleep(4)

    # Ana sayfadaki "Finansal Tablolar" tab'ına tıkla
    fin_tab_link = element_bul(driver, FIN_TAB_MENU_SELECTORS, bekleme=8)
    fin_tab_link.click()
    time.sleep(3)

    for sirket in sirket_listesi:
        print(f"\n>>> Şirket işleniyor: {sirket}")

        try:
            # ── Şirket adını gir ve Enter'a bas ──────────────────────────────
            sirket_input = element_bul(driver, SIRKET_INPUT_SELECTORS, bekleme)
            sirket_input.clear()
            time.sleep(0.5)
            sirket_input.send_keys(sirket, Keys.RETURN)
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
