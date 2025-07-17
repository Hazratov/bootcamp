from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
from datetime import datetime
from typing import List, Dict


class ChampionatParser:
    def __init__(self, headless=True):
        self.base_url = "https://championat.asia/oz/game-center/calendar"
        self.driver = self._setup_driver(headless)

    def _setup_driver(self, headless):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        return webdriver.Chrome(options=options)

    def get_games(self, date: str = None, sort: str = "any") -> List[Dict]:
        """O'yinlarni olish"""
        if not date:
            date = datetime.now().strftime("%d/%m/%Y")

        # URL formatini to'g'rilash
        url_date = self._convert_date_format(date)
        url = f"{self.base_url}?sort={sort}&date={url_date}"

        print(f"🔄 Sahifa yuklanmoqda: {url}")

        try:
            self.driver.get(url)

            # Sahifa yuklanishini kutish
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "match-center-list"))
            )

            return self._parse_games()

        except TimeoutException:
            print("⚠️ Sahifa yuklanmadi")
            return []
        except Exception as e:
            print(f"❌ Xato: {e}")
            return []

    def _convert_date_format(self, date: str) -> str:
        """DD/MM/YYYY -> YYYY-MM-DD"""
        try:
            dt = datetime.strptime(date, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except:
            return date

    def _parse_games(self) -> List[Dict]:
        """O'yinlarni parsing qilish"""
        games = []

        try:
            # Turnir bo'limlarini topish
            tournament_sections = self.driver.find_elements(By.CLASS_NAME, "tourney-name")
            game_tables = self.driver.find_elements(By.CSS_SELECTOR, "table.games-table")

            for i, table in enumerate(game_tables):
                tournament = tournament_sections[i].text.strip() if i < len(tournament_sections) else "Unknown"

                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    game = self._parse_game_row(row, tournament)
                    if game:
                        games.append(game)

        except Exception as e:
            print(f"❌ Parsing xatosi: {e}")

        return games

    def _parse_game_row(self, row, tournament: str) -> Dict:
        """Bitta o'yin qatorini parsing qilish"""
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 7:
                return None

            # Vaqt
            time_text = cells[0].text.strip()

            # Holat
            status = self._get_status(cells[1])

            # Jamoalar
            home_team = cells[2].text.strip()
            away_team = cells[6].text.strip()

            # Natija
            score = cells[4].text.strip()

            # Logotiplar
            home_logo = self._get_logo(cells[3])
            away_logo = self._get_logo(cells[5])

            # Havola
            link = self._get_link(cells[7])

            return {
                'id': row.get_attribute('id'),
                'tournament': tournament,
                'time': time_text,
                'status': status,
                'home_team': home_team,
                'away_team': away_team,
                'score': score,
                'home_logo': home_logo,
                'away_logo': away_logo,
                'link': link
            }

        except Exception as e:
            print(f"⚠️ Qator parsing xatosi: {e}")
            return None

    def _get_status(self, cell) -> Dict:
        """O'yin holatini aniqlash"""
        try:
            # Tugagan
            if cell.find_elements(By.CLASS_NAME, "matchcenter-sprite-finished"):
                return {"type": "finished", "text": "Tugagan"}

            # Bekor qilingan
            if cell.find_elements(By.CLASS_NAME, "matchcenter-sprite-cancelled"):
                return {"type": "cancelled", "text": "Bekor qilingan"}

            # Davom etayotgan
            live_spans = cell.find_elements(By.CSS_SELECTOR, "span[style*='color:red']")
            if live_spans:
                minute = live_spans[0].text.strip()
                return {"type": "live", "text": f"Davom etmoqda ({minute})"}

            # Boshlanmagan
            return {"type": "notstarted", "text": "Boshlanmagan"}

        except:
            return {"type": "unknown", "text": "Noma'lum"}

    def _get_logo(self, cell) -> str:
        """Logo URL ni olish"""
        try:
            img = cell.find_element(By.TAG_NAME, "img")
            return img.get_attribute('src')
        except:
            return None

    def _get_link(self, cell) -> str:
        """O'yin havolasini olish"""
        try:
            link = cell.find_element(By.TAG_NAME, "a")
            href = link.get_attribute('href')
            return href if href.startswith('http') else f"https://championat.asia{href}"
        except:
            return None

    def save_json(self, games: List[Dict], filename: str = "games.json"):
        """JSON ga saqlash"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
        print(f"💾 {len(games)} o'yin {filename} ga saqlandi")

    def print_games(self, games: List[Dict]):
        """Chiroyli chiqarish"""
        if not games:
            print("❌ Hech qanday o'yin topilmadi")
            return

        current_tournament = None
        for game in games:
            if game['tournament'] != current_tournament:
                current_tournament = game['tournament']
                print(f"\n🏆 {current_tournament}")
                print("-" * 50)

            status_emoji = {
                'finished': '✅',
                'live': '🔴',
                'notstarted': '⏱️',
                'cancelled': '❌'
            }.get(game['status']['type'], '❓')

            print(f"{status_emoji} {game['time']} | {game['home_team']} {game['score']} {game['away_team']}")

    def close(self):
        """Brauzerni yopish"""
        self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Foydalanish
if __name__ == "__main__":
    with ChampionatParser() as parser:
        # Misollar
        print("🚀 Boshlanmagan o'yinlar:")
        games = parser.get_games(date="18/07/2025", sort="any")
        parser.print_games(games)
        parser.save_json(games, "boshlanmagan_oyinlar.json")

        print("\n🔴 Davom etayotgan o'yinlar:")
        live_games = parser.get_games(sort="live", date="16/07/2025")
        parser.print_games(live_games)

        print("\n✅ Tugagan o'yinlar:")
        finished_games = parser.get_games(sort="finished")
        parser.print_games(finished_games)