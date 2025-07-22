# OPTIMIZED MATCH PARSER - championat/services/match_parser.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time
import logging


logger = logging.getLogger(__name__)


class MatchParserPool:
    """WebDriver pool bilan parser"""

    def __init__(self, pool_size=2):
        self.pool_size = pool_size
        self.drivers = []
        self.available_drivers = []
        self.lock = threading.Lock()
        self.base_url = "https://championat.asia/oz/game-center/calendar"

    def _create_driver(self):
        """Yangi driver yaratish"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        return webdriver.Chrome(options=options)

    def get_driver(self):
        """Pool dan driver olish"""
        with self.lock:
            if self.available_drivers:
                return self.available_drivers.pop()
            elif len(self.drivers) < self.pool_size:
                driver = self._create_driver()
                self.drivers.append(driver)
                return driver
            else:
                # Kutish
                return None

    def return_driver(self, driver):
        """Driver ni poolga qaytarish"""
        with self.lock:
            self.available_drivers.append(driver)

    def close_all(self):
        """Barcha driverlarni yopish"""
        with self.lock:
            for driver in self.drivers:
                try:
                    driver.quit()
                except:
                    pass
            self.drivers.clear()
            self.available_drivers.clear()


# Global pool
parser_pool = MatchParserPool()


class OptimizedMatchParser:
    def __init__(self, use_pool=True):
        self.base_url = "https://championat.asia/oz/game-center/calendar"
        self.use_pool = use_pool
        self.driver = None

    def __enter__(self):
        if self.use_pool:
            self.driver = parser_pool.get_driver()
            if not self.driver:
                # Pool to'liq bo'lsa, yangi driver yaratish
                self.driver = self._create_single_driver()
        else:
            self.driver = self._create_single_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.use_pool and self.driver:
            parser_pool.return_driver(self.driver)
        elif self.driver:
            self.driver.quit()

    def _create_single_driver(self):
        """Yakka driver yaratish"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        return webdriver.Chrome(options=options)

    def get_games(self, date: str = None, sort: str = "any") -> List[Dict]:
        """O'yinlarni olish (optimized)"""
        if not self.driver:
            return []

        if not date:
            date = datetime.now().strftime("%d/%m/%Y")

        url_date = self._convert_date_format(date)
        url = f"{self.base_url}?sort={sort}&date={url_date}"

        try:
            # Timeout qisqartirish
            self.driver.set_page_load_timeout(15)
            self.driver.get(url)

            # Sahifa yuklanishini kutish
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.CLASS_NAME, "match-center-list"))
            )

            return self._parse_games_optimized()

        except TimeoutException:
            logger.warning(f"Timeout: {url}")
            return []
        except Exception as e:
            logger.error(f"Parser error: {e}")
            return []

    def _convert_date_format(self, date: str) -> str:
        """DD/MM/YYYY -> YYYY-MM-DD"""
        try:
            dt = datetime.strptime(date, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except:
            return date

    def _parse_games_optimized(self) -> List[Dict]:
        """Optimized parsing"""
        games = []

        try:
            # Barcha turnir bo'limlarini bir vaqtda olish
            tournament_elements = self.driver.find_elements(By.CLASS_NAME, "tourney-name")
            tournaments = [elem.text.strip() for elem in tournament_elements]

            # Barcha jadvallarni olish
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table.games-table")

            for i, table in enumerate(tables):
                tournament = tournaments[i] if i < len(tournaments) else "Unknown"

                # Barcha qatorlarni bir vaqtda olish
                rows = table.find_elements(By.TAG_NAME, "tr")

                for row in rows:
                    game = self._parse_game_row_fast(row, tournament)
                    if game:
                        games.append(game)

        except Exception as e:
            logger.error(f"Parsing error: {e}")

        return games

    def _parse_game_row_fast(self, row, tournament: str) -> Optional[Dict]:
        """Tezroq parsing"""
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 7:
                return None

            # Barcha ma'lumotlarni bir vaqtda olish
            game_data = {
                'id': row.get_attribute('id') or f"game_{int(time.time())}",
                'tournament': tournament,
                'time': cells[0].text.strip(),
                'home_team': cells[2].text.strip(),
                'away_team': cells[6].text.strip(),
                'score': cells[4].text.strip(),
            }

            # Status
            game_data['status'] = self._get_status_fast(cells[1])

            # Logolar
            game_data['home_logo'] = self._get_logo_fast(cells[3])
            game_data['away_logo'] = self._get_logo_fast(cells[5])

            # Havola
            game_data['link'] = self._get_link_fast(cells[7])

            return game_data

        except Exception as e:
            logger.warning(f"Row parsing error: {e}")
            return None

    def _get_status_fast(self, cell) -> Dict:
        """Tez status aniqlash"""
        try:
            cell_html = cell.get_attribute('innerHTML')

            if 'matchcenter-sprite-finished' in cell_html:
                return {"type": "finished", "text": "Tugagan"}
            elif 'matchcenter-sprite-cancelled' in cell_html:
                return {"type": "cancelled", "text": "Bekor qilingan"}
            elif 'color:red' in cell_html:
                # Live match
                try:
                    minute = cell.text.strip()
                    return {"type": "live", "text": f"Davom etmoqda ({minute})"}
                except:
                    return {"type": "live", "text": "Davom etmoqda"}
            else:
                return {"type": "notstarted", "text": "Boshlanmagan"}

        except:
            return {"type": "unknown", "text": "Noma'lum"}

    def _get_logo_fast(self, cell) -> Optional[str]:
        """Tez logo olish"""
        try:
            img_elements = cell.find_elements(By.TAG_NAME, "img")
            if img_elements:
                src = img_elements[0].get_attribute('src')
                return src if src and src.startswith('http') else None
        except:
            pass
        return None

    def _get_link_fast(self, cell) -> Optional[str]:
        """Tez havola olish"""
        try:
            link_elements = cell.find_elements(By.TAG_NAME, "a")
            if link_elements:
                href = link_elements[0].get_attribute('href')
                if href:
                    return href if href.startswith('http') else f"https://championat.asia{href}"
        except:
            pass
        return None

    def get_matches_for_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Bir necha kunlik ma'lumotlarni olish"""
        all_games = []

        start = datetime.strptime(start_date, "%d/%m/%Y")
        end = datetime.strptime(end_date, "%d/%m/%Y")

        current = start
        while current <= end:
            date_str = current.strftime("%d/%m/%Y")
            games = self.get_games(date=date_str)
            all_games.extend(games)
            current += timedelta(days=1)

        return all_games


# Alias eski kodlar uchun
if __name__ == '__main__':
    with OptimizedMatchParser() as parser:
        matches = parser.get_matches_for_date_range("15/07/2025", "15/09/2025")

    for match in matches:
        print(match)