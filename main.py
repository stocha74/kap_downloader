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
