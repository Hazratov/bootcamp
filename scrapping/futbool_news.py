from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import re
import time


class ChampionatParser:
    def __init__(self, headless=True):
        self.base_url = "https://championat.asia"
        self.driver = self._setup_driver(headless)
        self.wait = WebDriverWait(self.driver, 10)

    def _setup_driver(self, headless):
        """Chrome driver sozlash"""
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(options=options)

    def get_news(self, url="https://championat.asia/oz"):
        """Yangiliklar olish"""
        try:
            self.driver.get(url)
            time.sleep(2)

            news_list = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "news-list"))
            )

            elements = news_list.find_elements(By.CLASS_NAME, "news-list-item")
            news_items = []

            for element in elements:
                try:
                    news_data = self._parse_news_item(element)
                    if news_data:
                        news_items.append(news_data)
                except Exception as e:
                    print(f"Yangilik parsing xatolik: {e}")
                    continue

            return news_items

        except Exception as e:
            print(f"Umumiy xatolik: {e}")
            return []

    def _parse_news_item(self, element):
        """Bitta yangilik elementini parsing"""
        try:
            summary_block = element.find_element(By.CLASS_NAME, "news-summary-block")

            # Asosiy ma'lumotlar
            title_elem = summary_block.find_element(By.CLASS_NAME, "main-link")
            title = title_elem.text.strip()

            # Rasm URL
            try:
                img = summary_block.find_element(By.TAG_NAME, "img")
                image_url = self.base_url + img.get_attribute("src")
            except NoSuchElementException:
                image_url = None

            # Qisqa tavsif
            try:
                summary = summary_block.find_element(By.CLASS_NAME, "summary").text.strip()
            except NoSuchElementException:
                summary = None

            # Sana va vaqt
            try:
                info_text = summary_block.find_element(By.CLASS_NAME, "info").text.strip()
                date_match = re.search(r'(\d{1,2}\s+\w+,\s+\d{2}:\d{2})', info_text)
                date_time = date_match.group(1) if date_match else None
            except NoSuchElementException:
                date_time = None

            # Yangilik turi
            news_type = "oddiy"
            try:
                tag_type = title_elem.find_element(By.CLASS_NAME, "tag-type")
                news_type = tag_type.text.strip().lower()
            except NoSuchElementException:
                pass

            # Detaillarni olish
            details = self._get_details(element)

            # Faqat kerakli fieldlar qaytarish
            result = {
                'title': title,
                'summary': summary,
                'image_url': image_url,
                'date_time': date_time,
                'news_type': news_type,
                'details': details
            }

            # None qiymatlarni olib tashlash
            return {k: v for k, v in result.items() if v is not None}

        except Exception as e:
            print(f"Element parsing xatolik: {e}")
            return None

    def _get_details(self, element):
        """Detaillarni olish"""
        details = {}

        try:
            # Load tugmasini bosish
            load_btn = element.find_element(By.CLASS_NAME, "load-item")
            if "loaded" not in load_btn.get_attribute("class"):
                self.driver.execute_script("arguments[0].click();", load_btn)
                time.sleep(1)

            # Description block
            desc_block = element.find_element(By.CLASS_NAME, "news-description-block")

            # To'liq matn
            try:
                details_div = desc_block.find_element(By.CLASS_NAME, "details")
                paragraphs = details_div.find_elements(By.TAG_NAME, "p")
                full_text = []
                for p in paragraphs:
                    text = p.text.strip()
                    if text:
                        full_text.append(text)
                if full_text:
                    details['full_text'] = '\n\n'.join(full_text)
            except NoSuchElementException:
                pass

            # Teglar
            try:
                tags_div = desc_block.find_element(By.CLASS_NAME, "tags")
                tag_links = tags_div.find_elements(By.TAG_NAME, "a")
                tags = [tag.text.strip() for tag in tag_links if tag.text.strip()]
                if tags:
                    details['tags'] = tags
            except NoSuchElementException:
                pass

            # Manba
            try:
                source_link = desc_block.find_element(By.CLASS_NAME, "source-link")
                source_div = source_link.find_element(By.CLASS_NAME, "source")
                source_text = source_div.text.strip()
                if ':' in source_text:
                    source = source_text.split(':', 1)[1].strip()
                    if source:
                        details['source'] = source
            except NoSuchElementException:
                pass

        except Exception as e:
            print(f"Details olishda xatolik: {e}")

        return details if details else None

    def save_json(self, news_items, filename="championat_news.json"):
        """JSON saqlaish"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, ensure_ascii=False, indent=2)
            print(f"✓ {len(news_items)} yangilik {filename} ga saqlandi")
        except Exception as e:
            print(f"✗ Saqlashda xatolik: {e}")

    def print_summary(self, news_items):
        """Qisqa xulosani chop etish"""
        print(f"\n=== CHAMPIONAT.ASIA YANGILIKLARI ===")
        print(f"Jami: {len(news_items)} ta yangilik")
        print("=" * 50)

        for i, news in enumerate(news_items, 1):
            print(f"{i}. {news['title']}")
            if news.get('date_time'):
                print(f"   Sana: {news['date_time']}")
            if news.get('details', {}).get('tags'):
                print(f"   Teglar: {', '.join(news['details']['tags'])}")
            print("-" * 50)

    def close(self):
        """Driver yopish"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def __del__(self):
        self.close()


# Foydalanish
def main():
    parser = ChampionatParser(headless=True)

    try:
        print("Yangiliklar olinmoqda...")
        news_items = parser.get_news()

        if news_items:
            # Xulosani chop etish
            parser.print_summary(news_items)

            # JSON saqlaish
            parser.save_json(news_items)

            # Birinchi yangilik namunasi
            print("\n=== BIRINCHI YANGILIK NAMUNASI ===")
            print(json.dumps(news_items[0], ensure_ascii=False, indent=2))

        else:
            print("Yangiliklar topilmadi!")

    except Exception as e:
        print(f"Xatolik: {e}")
    finally:
        parser.close()


if __name__ == "__main__":
    main()