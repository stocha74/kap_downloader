from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from utils import element_bul

KAP_ANA_URL = "https://www.kap.org.tr/tr"

# ── Olası selector listeleri ──────────────────────────────────────────────────

SIRKET_INPUT_SELECTORS = [
    (By.ID,           "search-input"),
    (By.XPATH,        "/html/body/main/section[1]/div/div/div[2]/div[2]/div/div/div[1]/div/div[1]/input"),
    (By.CSS_SELECTOR, "input[placeholder='Şirket Ünvanı']"),
]

ONERI_SELECTORS = [
    (By.CSS_SELECTOR, "#select-dropdown button"),
    (By.CSS_SELECTOR, "#select-dropdown ul li button"),
    (By.XPATH,        "(//*[@id='select-dropdown']//button)[1]"),
]

# Yıl dropdown açma butonu (div.select-button)
YIL_BUTON_SELECTORS = [
    (By.CSS_SELECTOR, "div.select-button"),
    (By.XPATH,        "//div[contains(@class,'select-button')]"),
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
            # ── Şirket adını gir, dropdown'dan ilk öneriyi seç ───────────────
            sirket_input = element_bul(driver, SIRKET_INPUT_SELECTORS, bekleme)
            sirket_input.clear()
            time.sleep(0.5)
            sirket_input.send_keys(sirket)
            time.sleep(2)  # Dropdown'ın yüklenmesini bekle

            oneri = element_bul(driver, ONERI_SELECTORS, bekleme)
            oneri.click()
            time.sleep(2)

            # ── Yıl dropdown'ını aç ve tüm yılları oku ───────────────────────
            yil_buton = element_bul(driver, YIL_BUTON_SELECTORS, bekleme)
            yil_buton.click()
            time.sleep(1)

            yil_label_els = driver.find_elements(By.CSS_SELECTOR, "ul.pt-0 li label")
            mevcut_yillar = sorted(
                [
                    lbl.text.strip()
                    for lbl in yil_label_els
                    if lbl.text.strip().isdigit()
                    and 2000 < int(lbl.text.strip()) <= 2025
                ],
                key=int,
                reverse=True,
            )
            print(f"  Bulunan yıllar: {mevcut_yillar}")

            # Dropdown'ı kapat
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)

            if not mevcut_yillar:
                print(f"  ⚠️  {sirket} için yıl bulunamadı, atlanıyor.")
                continue

            # ── İÇ LOOP: Her yıl için indir ──────────────────────────────────
            for yil in mevcut_yillar:
                print(f"  -> Yıl: {yil}")

                # Yıl dropdown'ını aç ve ilgili yıla tıkla
                yil_buton = element_bul(driver, YIL_BUTON_SELECTORS, bekleme)
                yil_buton.click()
                time.sleep(1)
                driver.find_element(
                    By.XPATH,
                    f"//ul[contains(@class,'pt-0')]//label[normalize-space()='{yil}']"
                ).click()
                time.sleep(1)

                # Periyot: Tüm Dönemler
                try:
                    from selenium.webdriver.support.ui import Select
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
