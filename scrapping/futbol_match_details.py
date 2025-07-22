import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re


class MatchDetailParser:
    def __init__(self, headless=False):
        self.driver = None
        self.wait = None
        self.setup_driver(headless)

        # Event type mappings based on CSS classes
        self.event_type_mapping = {
            'incident-14': 'goal',
            'incident-18': 'substitution',
            'incident-19': 'yellow_card',
            'incident-20': 'red_card',
            'incident-21': 'second_yellow_card'
        }

    def setup_driver(self, headless=False):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

    def parse_match(self, ext_id):
        """Parse match details for given ext_id"""
        try:
            match_data = {
                'ext_id': ext_id,
                'events': [],
                'home_team': {},
                'away_team': {}
            }

            # Parse events
            events_data = self.parse_events(ext_id)
            match_data['events'] = events_data

            # Parse lineups
            lineups_data = self.parse_lineups(ext_id)
            match_data.update(lineups_data)

            return match_data

        except Exception as e:
            print(f"Error parsing match {ext_id}: {str(e)}")
            return None

    def parse_events(self, ext_id):
        """Parse match events from events section"""
        main_url = f"https://championat.asia/oz/game-center/fixture/{ext_id}"

        try:
            self.driver.get(main_url)
            print(f"Loading main page: {main_url}")
            time.sleep(3)

            # Wait for the events container to be present
            try:
                events_container = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".game-incident-list"))
                )
            except TimeoutException:
                print("Events container not found")
                return []

            # Make sure the events are visible
            self.driver.execute_script("""
                var eventsList = document.querySelector('.game-incident-list');
                if (eventsList) {
                    eventsList.style.display = 'block';
                    eventsList.style.visibility = 'visible';
                }
            """)
            time.sleep(1)

            # Find the events table
            try:
                incidents_table = events_container.find_element(By.CSS_SELECTOR, ".incidents-table")
            except NoSuchElementException:
                print("Incidents table not found")
                return []

            events = []
            current_half = None

            # Get all rows from the table
            rows = incidents_table.find_elements(By.TAG_NAME, "tr")
            print(f"Found {len(rows)} rows in incidents table")

            for row_index, row in enumerate(rows):
                try:
                    # Check if this is a half separator
                    separator = row.find_elements(By.CSS_SELECTOR, ".table-separator")
                    if separator:
                        current_half = separator[0].text.strip()
                        print(f"Half separator found: {current_half}")
                        continue

                    # Get all cells in the row
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 5:  # Should have 5 columns based on HTML
                        continue

                    # Get minute from the green cell (index 2)
                    minute_cell = cells[2]
                    if "green" not in minute_cell.get_attribute("class"):
                        continue

                    minute = minute_cell.text.strip().replace("'", "")
                    if not minute:
                        continue

                    print(f"Processing row {row_index + 1}: minute {minute}")

                    # Check left side (home team) - cell index 0 and 1
                    left_cell = cells[0]  # Player info
                    left_icon_cell = cells[1]  # Event icon

                    if left_cell.text.strip():  # If there's content in left cell
                        event_icon = left_icon_cell.find_elements(By.CSS_SELECTOR, ".sm-event-icon")
                        if event_icon:
                            event_data = self._parse_event_from_cells(left_cell, event_icon[0], minute, current_half,
                                                                      "home")
                            if event_data:
                                events.append(event_data)
                                print(f"  Home event: {event_data['event_type']} - {event_data['player_name']}")

                    # Check right side (away team) - cell index 3 and 4
                    right_icon_cell = cells[3]  # Event icon
                    right_cell = cells[4]  # Player info

                    if right_cell.text.strip():  # If there's content in right cell
                        event_icon = right_icon_cell.find_elements(By.CSS_SELECTOR, ".sm-event-icon")
                        if event_icon:
                            event_data = self._parse_event_from_cells(right_cell, event_icon[0], minute, current_half,
                                                                      "away")
                            if event_data:
                                events.append(event_data)
                                print(f"  Away event: {event_data['event_type']} - {event_data['player_name']}")

                except Exception as e:
                    print(f"Error parsing row {row_index + 1}: {str(e)}")
                    continue

            print(f"Total events parsed: {len(events)}")
            return events

        except Exception as e:
            print(f"Error parsing events: {str(e)}")
            return []

    def _parse_event_from_cells(self, player_cell, icon_element, minute, half, team_side):
        """Parse event data from player cell and icon element"""
        try:
            # Get event type from icon classes
            icon_classes = icon_element.get_attribute("class")
            event_type = "unknown"

            for class_name, event_name in self.event_type_mapping.items():
                if class_name in icon_classes:
                    event_type = event_name
                    break

            # Get cell HTML to parse content
            cell_html = player_cell.get_attribute('innerHTML')
            cell_text = player_cell.text.strip()

            if not cell_text:
                return None

            print(f"    Parsing cell text: '{cell_text}'")
            print(f"    Event type: {event_type}")

            # Initialize variables
            player_name = ""
            assist = None
            score = None
            player_in = None
            player_out = None

            # Parse based on event type
            if event_type == "goal":
                # For goals: "Marquinhos 1-0\n(Nail Umyarov )"
                # Extract score from span with class "score"
                score_spans = player_cell.find_elements(By.CSS_SELECTOR, ".score")
                if score_spans:
                    score = score_spans[0].text.strip()

                # Extract assist from gray span
                gray_spans = player_cell.find_elements(By.CSS_SELECTOR, ".gray")
                if gray_spans:
                    assist_text = gray_spans[0].text.strip()
                    assist = assist_text.replace('(', '').replace(')', '').strip()

                # Extract player name (remove score if it exists in text)
                lines = cell_text.split('\n')
                if lines:
                    player_name = lines[0].strip()
                    # Remove score from player name if it exists
                    score_pattern = r'\s+\d+-\d+$'
                    player_name = re.sub(score_pattern, '', player_name).strip()

            elif event_type == "substitution":
                # For substitution: "Daniil Khlusevich\n(Pablo Solari)"
                lines = cell_text.split('\n')
                if len(lines) >= 2:
                    player_in = lines[0].strip()  # Player coming in
                    # Extract player going out from gray span or parentheses
                    gray_spans = player_cell.find_elements(By.CSS_SELECTOR, ".gray")
                    if gray_spans:
                        player_out_text = gray_spans[0].text.strip()
                        player_out = player_out_text.replace('(', '').replace(')', '').strip()

                    # For substitution, we'll create an event for the player coming in
                    player_name = player_in

            else:
                # For cards and other events: just the player name
                lines = cell_text.split('\n')
                if lines:
                    player_name = lines[0].strip()

            # Create event data
            event_data = {
                'minute': minute,
                'half': half,
                'event_type': event_type,
                'player_name': player_name,
                'team_side': team_side,
                'assist': assist,
                'score': score,
                'details': cell_text
            }

            # Add substitution specific data
            if event_type == "substitution" and player_out:
                event_data['player_out'] = player_out

            return event_data

        except Exception as e:
            print(f"    Error parsing event cell: {str(e)}")
            return None

    def parse_lineups(self, ext_id):
        """Parse team lineups from lineup section"""
        lineups_url = f"https://championat.asia/oz/game-center/fixture/lineup/load/{ext_id}"

        try:
            self.driver.get(lineups_url)
            time.sleep(3)

            # Wait for lineup container to load
            lineup_container = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".lineup-layout"))
            )

            # Find both team lineups
            lineup_sections = lineup_container.find_elements(By.CSS_SELECTOR, ".lineup")

            teams_data = {'home_team': {}, 'away_team': {}}
            team_keys = ['home_team', 'away_team']

            for i, lineup_section in enumerate(lineup_sections[:2]):
                team_key = team_keys[i]
                team_data = {
                    'coach': '',
                    'starting_lineup': [],
                    'substitutes': []
                }

                # Parse each position group
                separators = lineup_section.find_elements(By.CSS_SELECTOR, ".lineup-separator")
                tables = lineup_section.find_elements(By.CSS_SELECTOR, ".lineup-table")

                current_section = None

                for j, table in enumerate(tables):
                    if j < len(separators):
                        section_name = separators[j].text.strip().lower()
                        current_section = section_name

                    # Parse players in this table
                    rows = table.find_elements(By.TAG_NAME, "tr")

                    for row in rows:
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) < 3:
                                continue

                            # Extract player data
                            shirt_number = ''
                            photo_url = ''
                            player_name = ''
                            event_icons = []

                            # Get shirt number
                            rank_span = row.find_elements(By.CSS_SELECTOR, ".rank")
                            if rank_span:
                                shirt_number = rank_span[0].text.strip()

                            # Get photo URL
                            img_elements = row.find_elements(By.TAG_NAME, "img")
                            if img_elements:
                                photo_url = img_elements[0].get_attribute('src')

                            # Get player name
                            if len(cells) >= 3:
                                player_name = cells[2].text.strip()

                            # Get event icons
                            icon_elements = row.find_elements(By.CSS_SELECTOR, ".sm-event-icon")
                            for icon in icon_elements:
                                icon_classes = icon.get_attribute('class')
                                for class_name, event_name in self.event_type_mapping.items():
                                    if class_name in icon_classes:
                                        event_icons.append(event_name)

                            if not player_name:
                                continue

                            player_data = {
                                'player_name': player_name,
                                'shirt_number': shirt_number,
                                'photo_url': photo_url,
                                'event_icons': event_icons,
                                'position_group': current_section
                            }

                            # Categorize player
                            if current_section == 'murabbiy':  # Coach
                                team_data['coach'] = player_name
                            elif 'zaxira' in current_section.lower():  # Substitutes
                                team_data['substitutes'].append(player_data)
                            else:  # Starting lineup
                                team_data['starting_lineup'].append(player_data)

                        except Exception as e:
                            print(f"Error parsing player row: {str(e)}")
                            continue

                teams_data[team_key] = team_data

            return teams_data

        except TimeoutException:
            print(f"Timeout loading lineups for match {ext_id}")
            return {'home_team': {}, 'away_team': {}}
        except Exception as e:
            print(f"Error parsing lineups: {str(e)}")
            return {'home_team': {}, 'away_team': {}}

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Usage example
def main():
    ext_id = "19438666"

    with MatchDetailParser(headless=False) as parser:
        match_data = parser.parse_match(ext_id)

        if match_data:
            # Save to JSON file
            with open(f'match_{ext_id}.json', 'w', encoding='utf-8') as f:
                json.dump(match_data, f, ensure_ascii=False, indent=2)

            print(f"Match data saved to match_{ext_id}.json")
            print(f"\nMatch {ext_id} Summary:")
            print(f"Total events: {len(match_data['events'])}")
            print(f"Home team starting lineup: {len(match_data['home_team'].get('starting_lineup', []))}")
            print(f"Away team starting lineup: {len(match_data['away_team'].get('starting_lineup', []))}")

            # Print all events
            print(f"\nAll events:")
            for i, event in enumerate(match_data['events'], 1):
                assist_info = f" (Assist: {event['assist']})" if event.get('assist') else ""
                score_info = f" Score: {event['score']}" if event.get('score') else ""
                sub_info = f" (Out: {event['player_out']})" if event.get('player_out') else ""
                print(
                    f"  {i}. {event['minute']}' ({event['half']}) - {event['event_type']} - {event['player_name']} ({event['team_side']}){assist_info}{score_info}{sub_info}")
        else:
            print("Failed to parse match data")


if __name__ == "__main__":
    main()