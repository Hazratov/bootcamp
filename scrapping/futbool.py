from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime


class ChampionatSeleniumParser:
    def __init__(self, headless=True):
        self.base_url = "https://championat.asia"
        self.setup_driver(headless)

    def setup_driver(self, headless=True):
        """Chrome driverini sozlash"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def get_page_content(self, url):
        """Sahifani yuklash"""
        try:
            self.driver.get(url)
            time.sleep(2)  # Sahifa to'liq yuklanishini kutish
            return True
        except Exception as e:
            print(f"Sahifani yuklashda xatolik: {e}")
            return False

    def parse_news_list(self):
        """Yangiliklar ro'yxatini parsing qilish"""
        news_items = []

        try:
            # Yangiliklar ro'yxatini topish
            news_list = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "news-list"))
            )

            # Har bir yangilik elementini topish
            news_elements = news_list.find_elements(By.CLASS_NAME, "news-list-item")
            print(f"Jami {len(news_elements)} ta yangilik topildi")

            for i, element in enumerate(news_elements):
                try:
                    print(f"Yangilik {i + 1}/{len(news_elements)} ishlanmoqda...")
                    news_data = self.parse_single_news(element)
                    if news_data:
                        news_items.append(news_data)
                        print(f"✓ Muvaffaqiyatli: {news_data['title'][:50]}...")
                    else:
                        print("✗ Yangilik ma'lumotlari olinmadi")
                except Exception as e:
                    print(f"✗ Yangilik {i + 1} da xatolik: {e}")
                    continue

        except TimeoutException:
            print("Yangiliklar ro'yxati topilmadi")
            return []
        except Exception as e:
            print(f"Yangiliklar ro'yxatini parsing qilishda xatolik: {e}")
            return []

        return news_items

    def parse_single_news(self, element):
        """Bitta yangilik elementini parsing qilish"""
        try:
            # Asosiy ma'lumotlarni olish
            summary_block = element.find_element(By.CLASS_NAME, "news-summary-block")

            # Rasm URL'ini olish
            try:
                img_element = summary_block.find_element(By.TAG_NAME, "img")
                image_url = self.base_url + img_element.get_attribute("src")
            except NoSuchElementException:
                image_url = None

            # Sarlavhani olish
            try:
                title_element = summary_block.find_element(By.CLASS_NAME, "main-link")
                title = title_element.text.strip()
                article_url = title_element.get_attribute("href")
            except NoSuchElementException:
                title = None
                article_url = None

            # Qisqa tavsifni olish
            try:
                summary_element = summary_block.find_element(By.CLASS_NAME, "summary")
                summary = summary_element.text.strip()
            except NoSuchElementException:
                summary = None

            # Sana, vaqt, ko'rishlar va izohlar sonini olish
            try:
                info_element = summary_block.find_element(By.CLASS_NAME, "info")
                info_text = info_element.text.strip()

                # Sana va vaqtni ajratish
                date_match = re.search(r'(\d{1,2}\s+\w+,\s+\d{2}:\d{2})', info_text)
                date_time = date_match.group(1) if date_match else None

                # Ko'rishlar va izohlar sonini olish
                try:
                    comments_element = info_element.find_element(By.CLASS_NAME, "comments")
                    comments_text = comments_element.text.strip()

                    # Ko'rishlar sonini olish (birinchi raqam)
                    views_match = re.search(r'(\d+)', comments_text)
                    views = int(views_match.group(1)) if views_match else 0

                    # Izohlar sonini olish (ikkinchi raqam)
                    numbers = re.findall(r'\d+', comments_text)
                    comments = int(numbers[1]) if len(numbers) > 1 else 0

                except NoSuchElementException:
                    views = 0
                    comments = 0

            except NoSuchElementException:
                date_time = None
                views = 0
                comments = 0

            # Item ID ni olish
            try:
                buttons_div = element.find_element(By.CLASS_NAME, "buttons")
                load_button = buttons_div.find_element(By.CLASS_NAME, "load-item")
                item_id = load_button.get_attribute("data-item")
            except NoSuchElementException:
                item_id = None

            # Yangilik turini aniqlash
            news_type = "oddiy"
            try:
                if title_element:
                    tag_type = title_element.find_element(By.CLASS_NAME, "tag-type")
                    news_type = tag_type.text.strip().lower()
            except NoSuchElementException:
                pass

            # Hide qilingan detaillarni olish
            details = self.get_hidden_details(element)

            return {
                'title': title,
                'summary': summary,
                'image_url': image_url,
                'article_url': article_url,
                'date_time': date_time,
                'views': views,
                'comments': comments,
                'news_type': news_type,
                'item_id': item_id,
                'details': details
            }

        except Exception as e:
            print(f"Yangilik parsing qilishda xatolik: {e}")
            return None

    def get_hidden_details(self, element):
        """Hide qilingan detaillarni olish"""
        details = {
            'full_text': None,
            'tags': [],
            'source': None,
            'telegram_link': None,
            'share_links': {}
        }

        try:
            # "yangilikni ko'rsatish" tugmasini topish va bosish
            buttons_div = element.find_element(By.CLASS_NAME, "buttons")
            load_button = buttons_div.find_element(By.CLASS_NAME, "load-item")

            # Tugma allaqachon bosilganmi tekshirish
            if "loaded" not in load_button.get_attribute("class"):
                print("  'Yangilikni ko'rsatish' tugmasi bosilmoqda...")

                # Tugmani bosish
                self.driver.execute_script("arguments[0].click();", load_button)

                # Kontent yuklanishini kutish
                time.sleep(2)

                # Yuklanish tugmasini kutish
                try:
                    self.wait.until(
                        lambda driver: "loaded" in load_button.get_attribute("class")
                    )
                except TimeoutException:
                    print("  Tugma yuklanishi kutildi, lekin vaqt tugadi")

            # Hide qilingan blokni topish
            try:
                description_block = element.find_element(By.CLASS_NAME, "news-description-block")

                # Blok ko'rinadigan bo'lishini kutish
                if description_block.value_of_css_property("display") == "none":
                    print("  Description block hali yashirin, kutilmoqda...")
                    time.sleep(1)

                # To'liq matnni olish
                try:
                    details_div = description_block.find_element(By.CLASS_NAME, "details")
                    paragraphs = details_div.find_elements(By.TAG_NAME, "p")
                    full_text = []
                    for p in paragraphs:
                        text = p.text.strip()
                        if text:
                            full_text.append(text)
                    details['full_text'] = '\n\n'.join(full_text)
                    print(f"  ✓ To'liq matn olindi: {len(details['full_text'])} belgi")
                except NoSuchElementException:
                    print("  Details div topilmadi")

                # Teglarni olish
                try:
                    tags_div = description_block.find_element(By.CLASS_NAME, "tags")
                    tag_links = tags_div.find_elements(By.TAG_NAME, "a")
                    for tag_link in tag_links:
                        tag_text = tag_link.text.strip()
                        if tag_text:
                            details['tags'].append(tag_text)
                    print(f"  ✓ Teglar olindi: {len(details['tags'])} ta")
                except NoSuchElementException:
                    print("  Teglar topilmadi")

                # Manba ma'lumotini olish
                try:
                    source_link = description_block.find_element(By.CLASS_NAME, "source-link")
                    source_div = source_link.find_element(By.CLASS_NAME, "source")
                    source_text = source_div.text.strip()
                    if ':' in source_text:
                        details['source'] = source_text.split(':', 1)[1].strip()
                        print(f"  ✓ Manba: {details['source']}")
                except NoSuchElementException:
                    print("  Manba topilmadi")

                # Telegram linkini olish
                try:
                    telegram_link = description_block.find_element(
                        By.XPATH, ".//a[contains(@href, 'telegram.me')]"
                    )
                    details['telegram_link'] = telegram_link.get_attribute("href")
                    print("  ✓ Telegram linki olindi")
                except NoSuchElementException:
                    print("  Telegram linki topilmadi")

                # Ijtimoiy tarmoq linklatini olish
                try:
                    share_box = description_block.find_element(By.CLASS_NAME, "share-box")
                    share_links = share_box.find_elements(By.TAG_NAME, "a")
                    for link in share_links:
                        classes = link.get_attribute("class")
                        if classes:
                            for platform in ['facebook', 'twitter', 'vkontakte', 'odnoklassniki']:
                                if platform in classes:
                                    details['share_links'][platform] = link.get_attribute("href")
                    print(f"  ✓ Ijtimoiy tarmoq linklari: {len(details['share_links'])} ta")
                except NoSuchElementException:
                    print("  Ijtimoiy tarmoq linklari topilmadi")

            except NoSuchElementException:
                print("  News description block topilmadi")

        except NoSuchElementException:
            print("  Load tugmasi topilmadi")
        except ElementClickInterceptedException:
            print("  Tugmani bosishda xatolik")
        except Exception as e:
            print(f"  Detaillarni olishda xatolik: {e}")

        return details

    def get_all_news(self, url="https://championat.asia/oz"):
        """Barcha yangiliklarni olish"""
        if not self.get_page_content(url):
            return []

        news_items = self.parse_news_list()
        print(f"\nJami {len(news_items)} ta yangilik muvaffaqiyatli olinldi")

        return news_items

    def save_to_json(self, news_items, filename="championat_news_selenium.json"):
        """Yangilikларni JSON faylga saqlash"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(news_items, f, ensure_ascii=False, indent=2)
            print(f"✓ Yangiliklar {filename} faylga saqlandi")
        except Exception as e:
            print(f"✗ Faylga saqlashda xatolik: {e}")

    def print_news_summary(self, news_items):
        """Yangiliklar xulosasini chop etish"""
        print(f"\n=== CHAMPIONAT.ASIA YANGILIKLARI (SELENIUM) ===")
        print(f"Jami yangiliklar soni: {len(news_items)}")
        print("=" * 50)

        for i, news in enumerate(news_items, 1):
            print(f"\n{i}. {news['title']}")
            print(f"   Qisqa tavsif: {news['summary']}")
            print(f"   Sana: {news['date_time']}")
            print(f"   Ko'rishlar: {news['views']}, Izohlar: {news['comments']}")
            print(f"   Turi: {news['news_type']}")
            print(f"   Item ID: {news['item_id']}")
            print(f"   Havola: {news['article_url']}")

            # Detallari
            if news['details']:
                details = news['details']
                if details['full_text']:
                    print(f"   To'liq matn: {details['full_text'][:200]}...")
                if details['tags']:
                    print(f"   Teglar: {', '.join(details['tags'])}")
                if details['source']:
                    print(f"   Manba: {details['source']}")
                if details['telegram_link']:
                    print(f"   Telegram: {details['telegram_link']}")
                if details['share_links']:
                    print(f"   Ijtimoiy tarmoqlar: {list(details['share_links'].keys())}")

            print("-" * 50)

    def print_detailed_news(self, news_items):
        """Yangiliklar detallari bilan to'liq chop etish"""
        print(f"\n=== CHAMPIONAT.ASIA YANGILIKLARI (DETALLARI BILAN) ===")
        print(f"Jami yangiliklar soni: {len(news_items)}")
        print("=" * 80)

        for i, news in enumerate(news_items, 1):
            print(f"\n{i}. {news['title']}")
            print(f"Sana: {news['date_time']}")
            print(f"Ko'rishlar: {news['views']}, Izohlar: {news['comments']}")
            print(f"Turi: {news['news_type']}")
            print(f"Item ID: {news['item_id']}")
            print(f"Havola: {news['article_url']}")

            if news['summary']:
                print(f"\nQisqa tavsif: {news['summary']}")

            # Detallari
            if news['details']:
                details = news['details']

                if details['full_text']:
                    print(f"\nTo'liq matn:\n{details['full_text']}")

                if details['tags']:
                    print(f"\nTeglar: {', '.join(details['tags'])}")

                if details['source']:
                    print(f"Manba: {details['source']}")

                if details['telegram_link']:
                    print(f"Telegram: {details['telegram_link']}")

                if details['share_links']:
                    print(f"Ijtimoiy tarmoqlar:")
                    for platform, link in details['share_links'].items():
                        print(f"  {platform}: {link}")

            print("=" * 80)

    def search_news_by_keyword(self, news_items, keyword):
        """Kalit so'z bo'yicha yangilik qidirish"""
        found_news = []
        keyword_lower = keyword.lower()

        for news in news_items:
            # Sarlavhada qidirish
            if keyword_lower in news['title'].lower():
                found_news.append(news)
                continue

            # Qisqa tavsifda qidirish
            if news['summary'] and keyword_lower in news['summary'].lower():
                found_news.append(news)
                continue

            # To'liq matndagi qidirish
            if news['details'] and news['details']['full_text']:
                if keyword_lower in news['details']['full_text'].lower():
                    found_news.append(news)
                    continue

            # Teglarda qidirish
            if news['details'] and news['details']['tags']:
                for tag in news['details']['tags']:
                    if keyword_lower in tag.lower():
                        found_news.append(news)
                        break

        return found_news

    def get_statistics(self, news_items):
        """Statistika ma'lumotlarini olish"""
        if not news_items:
            return {}

        total_views = sum(news['views'] for news in news_items if news['views'])
        total_comments = sum(news['comments'] for news in news_items if news['comments'])

        most_viewed = max(news_items, key=lambda x: x['views'] or 0)
        most_commented = max(news_items, key=lambda x: x['comments'] or 0)

        detailed_news = [news for news in news_items if news['details']['full_text']]

        return {
            'total_news': len(news_items),
            'total_views': total_views,
            'total_comments': total_comments,
            'most_viewed': most_viewed,
            'most_commented': most_commented,
            'detailed_news_count': len(detailed_news),
            'detailed_news_percent': (len(detailed_news) / len(news_items)) * 100
        }

    def close(self):
        """Driverni yopish"""
        if hasattr(self, 'driver'):
            self.driver.quit()

    def __del__(self):
        """Destruktor - driverni avtomatik yopish"""
        self.close()


# Foydalanish misoli
def main():
    parser = None

    try:
        print("Selenium driver ishga tushirilmoqda...")
        parser = ChampionatSeleniumParser(headless=False)  # headless=True - ko'rinmas rejim

        # Yangilikəları olish
        print("Yangiliklar olinmoqda...")
        news_items = parser.get_all_news()

        if news_items:
            # Yangiliklar xulosasini chop etish
            parser.print_news_summary(news_items)

            # JSON faylga saqlash
            parser.save_to_json(news_items)

            # Statistika
            stats = parser.get_statistics(news_items)
            print(f"\nSTATISTIKA:")
            print(f"Jami yangiliklar: {stats['total_news']}")
            print(f"Jami ko'rishlar: {stats['total_views']}")
            print(f"Jami izohlar: {stats['total_comments']}")
            print(f"Detallari bor yangiliklar: {stats['detailed_news_count']} ({stats['detailed_news_percent']:.1f}%)")
            print(f"Eng ko'p ko'rilgan: {stats['most_viewed']['title']} ({stats['most_viewed']['views']} ko'rish)")
            print(f"Eng ko'p izohli: {stats['most_commented']['title']} ({stats['most_commented']['comments']} izoh)")

            # Birinchi yangilik detallari bilan
            print("\n" + "=" * 50)
            print("BIRINCHI YANGILIK DETALLARI:")
            print("=" * 50)
            parser.print_detailed_news([news_items[0]])

            # Kalit so'z bo'yicha qidirish
            print("\n" + "=" * 50)
            print("'FUTBOL' KALIT SO'ZI BO'YICHA QIDIRISH:")
            print("=" * 50)
            football_news = parser.search_news_by_keyword(news_items, "futbol")
            if football_news:
                print(f"Topilgan yangiliklar: {len(football_news)}")
                for news in football_news[:3]:
                    print(f"- {news['title']}")
            else:
                print("Hech qanday yangilik topilmadi")

        else:
            print("Yangiliklar topilmadi yoki parsing xatoligi!")

    except Exception as e:
        print(f"Umumiy xatolik: {e}")

    finally:
        if parser:
            parser.close()
            print("Driver yopildi")


def quick_test():
    """Tezkor test - birinchi 3 ta yangilik"""
    parser = None

    try:
        print("Tezkor test boshlanmoqda...")
        parser = ChampionatSeleniumParser(headless=True)

        if parser.get_page_content("https://championat.asia/oz"):
            news_items = parser.parse_news_list()

            # Faqat birinchi 3 ta yangilik
            if news_items:
                limited_news = news_items[:3]
                print(f"Tezkor test: {len(limited_news)} ta yangilik:")
                for i, news in enumerate(limited_news, 1):
                    print(f"{i}. {news['title']}")
                    print(f"   Detallari: {'✓' if news['details']['full_text'] else '✗'}")
                    print(f"   Teglar: {len(news['details']['tags'])} ta")
                    print(f"   Manba: {news['details']['source'] or 'Yoq'}")
                    print()
            else:
                print("Yangiliklar topilmadi")

    except Exception as e:
        print(f"Tezkor test xatoligi: {e}")

    finally:
        if parser:
            parser.close()


if __name__ == "__main__":
    main()
    # quick_test()  # Tezkor test uchun