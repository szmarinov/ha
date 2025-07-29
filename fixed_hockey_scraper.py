#!/usr/bin/env python3
"""
🏒 ENHANCED HOCKEY ARENA INTELLIGENT SCRAPER
===========================================
Интелигентен scraper с AI анализи и препоръки за Hockey Arena
Версия: 2.0 - Enhanced Edition
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import re
import csv
import random
import math
from typing import Dict, List, Optional, Tuple
import logging

# Настройка на logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntelligentHockeyAnalyzer:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = "https://www.hockeyarena.net"
        
        # Интелигентна структура за данни
        self.data = {
            'team_info': {},
            'players': [],
            'youth_players': [],
            'market_data': [],
            'finances': {},
            'tactics': {},
            'training': {},
            'matches': [],
            'standings': {},
            'statistics': {},
            'ai_analysis': {},
            'recommendations': [],
            'transfer_targets': [],
            'tactical_suggestions': [],
            'training_plan': {}
        }
        
        # Human-like headers за избягване на detection
        self.session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept-Language': 'bg-BG,bg;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        # Страниците за анализ с приоритет
        self.analysis_pages = {
            'critical': {
                'players': 'manager_team_players.php',
                'finances': 'manager_finance_report.inc',
                'tactics': 'manager_tactics_form.php',
                'market': 'manager_market_list.php',
                'youth_school': 'manager_youthacademy_players.php'
            },
            'important': {
                'training': 'manager_training_form1.php',
                'matches': 'manager_matches.php',
                'standings': 'public_standings.inc',
                'statistics': 'manager_team_statistics.php'
            },
            'optional': {
                'calendar': 'manager_calendar.php',
                'stadium': 'manager_stadium.php',
                'scouting': 'manager_scouting.php',
                'lineup': 'manager_lineup.php'
            }
        }
        
        # Хокейни позиции и важност на атрибутите
        self.position_weights = {
            'goalkeeper': {'goa': 0.4, 'def': 0.2, 'str': 0.2, 'spe': 0.1, 'att': 0.05, 'sho': 0.05, 'pas': 0.0},
            'defenseman': {'def': 0.3, 'str': 0.25, 'pas': 0.2, 'goa': 0.0, 'spe': 0.15, 'att': 0.05, 'sho': 0.05},
            'forward': {'att': 0.25, 'sho': 0.25, 'spe': 0.2, 'pas': 0.15, 'str': 0.1, 'def': 0.05, 'goa': 0.0},
            'center': {'pas': 0.25, 'att': 0.2, 'sho': 0.2, 'spe': 0.15, 'str': 0.1, 'def': 0.1, 'goa': 0.0}
        }

    def _get_random_user_agent(self) -> str:
        """Връща случаен user agent за имитиране на различни браузъри"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)

    def _human_delay(self, min_seconds: float = 1.5, max_seconds: float = 4.0):
        """Човешки delay между заявките"""
        delay = random.uniform(min_seconds, max_seconds)
        # Понякога правим по-дълги паузи като истински потребител
        if random.random() < 0.1:  # 10% шанс за по-дълга пауза
            delay += random.uniform(2.0, 5.0)
        
        logger.info(f"💤 Human delay: {delay:.1f}s")
        time.sleep(delay)

    def _simulate_human_browsing(self):
        """Симулира човешко поведение - случайни движения на мишката, скролиране и т.н."""
        # Симулираме размисъл време
        think_time = random.uniform(0.5, 2.0)
        time.sleep(think_time)

    def login(self) -> bool:
        """Подобрено логване с човешко поведение"""
        print(f"🔐 Attempting intelligent login for user: {self.username}")
        
        try:
            # Първо зареждаме главната страница
            print("📍 Loading homepage...")
            self._human_delay(1.0, 2.0)
            
            home_response = self.session.get(f"{self.base_url}/")
            if home_response.status_code != 200:
                logger.error(f"Failed to load homepage: {home_response.status_code}")
                return False
                
            # Симулираме разглеждане на страницата
            self._simulate_human_browsing()
            
            # Отиваме до login страницата
            print("📍 Navigating to login page...")
            self._human_delay()
            
            login_url = f"{self.base_url}/index.php?p=login&lang=6"
            login_page = self.session.get(login_url)
            
            if login_page.status_code != 200:
                logger.error(f"Failed to load login page: {login_page.status_code}")
                return False
                
            # Парсваме login формата
            soup = BeautifulSoup(login_page.content, 'html.parser')
            form = soup.find('form')
            
            if not form:
                logger.error("Login form not found")
                return False
                
            # Симулираме попълване на формата
            print("⌨️  Filling login form...")
            self._human_delay(2.0, 4.0)  # Време за въвеждане на данните
            
            # Подготвяме login данните
            login_data = {
                'nick': self.username,
                'password': self.password,
                'login': 'Влизане'
            }
            
            # Добавяме скрити полета от формата
            for input_tag in form.find_all('input', {'type': 'hidden'}):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    login_data[name] = value
            
            # Правим login заявката
            print("🚀 Submitting login...")
            self._human_delay(1.0, 2.0)
            
            login_response = self.session.post(
                f"{self.base_url}/index.php",
                data=login_data,
                allow_redirects=True
            )
            
            # Проверяваме дали сме влезли успешно
            if 'manager' in login_response.url.lower() or 'мениджър' in login_response.text:
                print("✅ Login successful!")
                self._human_delay()
                return True
            else:
                logger.error("Login failed - check credentials")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def calculate_player_rating(self, player_data: Dict, position: str = 'forward') -> float:
        """Изчислява интелигентен рейтинг на играч според позицията"""
        try:
            # Извличаме атрибутите
            attributes = {}
            for key, value in player_data.items():
                if key.lower() in ['goa', 'def', 'att', 'sho', 'spe', 'str', 'pas']:
                    try:
                        # Парсваме числата от текста
                        numbers = re.findall(r'\d+', str(value))
                        if numbers:
                            attributes[key.lower()] = int(numbers[0])
                    except:
                        continue
            
            if not attributes:
                return 0.0
            
            # Определяме позицията ако не е зададена
            if position == 'forward' and any(keyword in str(player_data).lower() for keyword in ['вратар', 'goalkeeper', 'gk']):
                position = 'goalkeeper'
            elif position == 'forward' and any(keyword in str(player_data).lower() for keyword in ['защитник', 'defenseman', 'def']):
                position = 'defenseman'
            
            # Използваме тежестите за позицията
            weights = self.position_weights.get(position, self.position_weights['forward'])
            
            # Изчисляваме претегления рейтинг
            total_rating = 0.0
            total_weight = 0.0
            
            for attr, weight in weights.items():
                if attr in attributes and weight > 0:
                    total_rating += attributes[attr] * weight
                    total_weight += weight
            
            if total_weight > 0:
                return round(total_rating / total_weight, 1)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating player rating: {str(e)}")
            return 0.0

    def analyze_market_opportunities(self) -> List[Dict]:
        """Анализира трансферния пазар за възможности"""
        opportunities = []
        
        for player in self.data['market_data']:
            try:
                # Изчисляваме рейтинга на играча
                rating = self.calculate_player_rating(player)
                
                # Парсваме цената
                price_text = player.get('мин. цена', '0')
                price = 0
                
                price_numbers = re.findall(r'[\d\s]+', price_text.replace(',', '').replace(' ', ''))
                if price_numbers:
                    try:
                        price = int(''.join(price_numbers[0].split()))
                    except:
                        price = 0
                
                # Парсваме възрастта
                age = 30  # default
                age_text = player.get('възраст', '30')
                age_match = re.search(r'\d+', str(age_text))
                if age_match:
                    age = int(age_match.group())
                
                # Изчисляваме value for money
                if price > 0 and rating > 0:
                    value_ratio = rating / (price / 1000000)  # rating per million
                    age_factor = max(0.5, (35 - age) / 10)  # younger is better
                    
                    opportunity_score = value_ratio * age_factor
                    
                    if opportunity_score > 5:  # Добра възможност
                        opportunities.append({
                            'player': player.get('име', 'Unknown'),
                            'rating': rating,
                            'price': price,
                            'age': age,
                            'value_ratio': round(value_ratio, 2),
                            'opportunity_score': round(opportunity_score, 2),
                            'recommendation': self._get_transfer_recommendation(rating, price, age)
                        })
                        
            except Exception as e:
                logger.error(f"Error analyzing market player: {str(e)}")
                continue
        
        # Сортираме по opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        return opportunities[:10]  # Топ 10

    def _get_transfer_recommendation(self, rating: float, price: int, age: int) -> str:
        """Генерира препоръка за трансфер"""
        if age < 22 and rating > 50:
            return "🌟 Млад талант с потенциал - СИЛНО препоръчително!"
        elif rating > 70 and price < 10000000:
            return "💰 Отлично съотношение цена/качество"
        elif age > 32 and price > 20000000:
            return "⚠️ Висока цена за възрастен играч - внимание!"
        elif rating > 60:
            return "✅ Добро попълнение за отбора"
        else:
            return "❌ Не се препоръчва"

    def analyze_team_strengths_weaknesses(self) -> Dict:
        """Анализира силните и слабите места на отбора"""
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'position_analysis': {},
            'age_analysis': {},
            'overall_rating': 0.0
        }
        
        if not self.data['players']:
            return analysis
        
        # Анализ по позиции
        position_stats = {}
        total_rating = 0.0
        ages = []
        
        for player in self.data['players']:
            # Определяме позицията
            position = 'forward'  # default
            player_text = str(player).lower()
            
            if any(keyword in player_text for keyword in ['вратар', 'goalkeeper']):
                position = 'goalkeeper'
            elif any(keyword in player_text for keyword in ['защитник', 'defenseman']):
                position = 'defenseman'
            
            # Изчисляваме рейтинга
            rating = self.calculate_player_rating(player, position)
            total_rating += rating
            
            if position not in position_stats:
                position_stats[position] = {'count': 0, 'total_rating': 0.0, 'players': []}
            
            position_stats[position]['count'] += 1
            position_stats[position]['total_rating'] += rating
            position_stats[position]['players'].append({
                'name': player.get('име', 'Unknown'),
                'rating': rating
            })
            
            # Възраст
            age_text = player.get('възраст', '30')
            age_match = re.search(r'\d+', str(age_text))
            if age_match:
                ages.append(int(age_match.group()))
        
        # Изчисляваме средни рейтинги по позиции
        for position, stats in position_stats.items():
            if stats['count'] > 0:
                avg_rating = stats['total_rating'] / stats['count']
                analysis['position_analysis'][position] = {
                    'average_rating': round(avg_rating, 1),
                    'player_count': stats['count'],
                    'top_player': max(stats['players'], key=lambda x: x['rating']) if stats['players'] else None
                }
                
                # Определяме силни/слаби места
                if avg_rating > 65:
                    analysis['strengths'].append(f"Силна {position} позиция (рейтинг: {avg_rating:.1f})")
                elif avg_rating < 45:
                    analysis['weaknesses'].append(f"Слаба {position} позиция (рейтинг: {avg_rating:.1f})")
        
        # Възрастов анализ
        if ages:
            avg_age = sum(ages) / len(ages)
            analysis['age_analysis'] = {
                'average_age': round(avg_age, 1),
                'youngest': min(ages),
                'oldest': max(ages)
            }
            
            if avg_age > 30:
                analysis['weaknesses'].append(f"Стар отбор (средна възраст: {avg_age:.1f})")
            elif avg_age < 25:
                analysis['strengths'].append(f"Млад отбор с потенциал (средна възраст: {avg_age:.1f})")
        
        # Общ рейтинг
        if len(self.data['players']) > 0:
            analysis['overall_rating'] = round(total_rating / len(self.data['players']), 1)
        
        return analysis

    def generate_training_plan(self) -> Dict:
        """Генерира интелигентен план за тренировки"""
        team_analysis = self.analyze_team_strengths_weaknesses()
        plan = {
            'priorities': [],
            'weekly_schedule': {},
            'focus_areas': [],
            'long_term_goals': []
        }
        
        # Базираме се на слабите места
        for weakness in team_analysis['weaknesses']:
            if 'защитник' in weakness.lower() or 'defenseman' in weakness.lower():
                plan['priorities'].append("🛡️ Подобряване на защитата")
                plan['focus_areas'].append("Тренировки за DEF и STR")
            elif 'нападател' in weakness.lower() or 'forward' in weakness.lower():
                plan['priorities'].append("⚽ Подобряване на атаката")
                plan['focus_areas'].append("Тренировки за ATT и SHO")
            elif 'вратар' in weakness.lower() or 'goalkeeper' in weakness.lower():
                plan['priorities'].append("🥅 Подобряване на вратарската игра")
                plan['focus_areas'].append("Тренировки за GOA")
        
        # Възрастови препоръки
        if team_analysis['age_analysis'].get('average_age', 25) > 29:
            plan['long_term_goals'].append("🔄 Подмяна на стари играчи с млади таланти")
            plan['priorities'].append("💪 Поддържане на физическата форма")
        
        # Седмичен график
        plan['weekly_schedule'] = {
            'Понеделник': 'Кардио тренировка (SPE)',
            'Вторник': 'Техническа подготовка (PAS)',
            'Сряда': 'Почивка',
            'Четвъртък': 'Силова тренировка (STR)',
            'Петък': 'Тактическа подготовка',
            'Събота': 'Подготовка за мач',
            'Неделя': 'Мач или почивка'
        }
        
        return plan

    def scrape_page_intelligently(self, page_name: str, page_url: str) -> bool:
        """Интелигентно скрейпване на страница с анализ"""
        print(f"🧠 Intelligently analyzing: {page_name}")
        
        try:
            # Човешки delay преди заявката
            self._human_delay()
            
            # Правим заявката
            url = f"{self.base_url}/{page_url}"
            response = self.session.get(url)
            
            if response.status_code != 200:
                logger.error(f"Failed to load {page_name}: {response.status_code}")
                return False
            
            # Запазваме HTML за debug
            with open(f"{page_name}_page.html", 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Специализиран анализ според типа страница
            success = False
            
            if page_name == 'players':
                success = self._analyze_players_intelligently(soup)
            elif page_name == 'market':
                success = self._analyze_market_intelligently(soup)
            elif page_name == 'youth_school':
                success = self._analyze_youth_intelligently(soup)
            elif page_name == 'finances':
                success = self._analyze_finances_intelligently(soup)
            elif page_name == 'tactics':
                success = self._analyze_tactics_intelligently(soup)
            else:
                success = self._generic_page_analysis(soup, page_name)
            
            if success:
                print(f"     ✅ {page_name} analyzed successfully")
            else:
                print(f"     ⚠️ {page_name} analysis incomplete")
            
            return success
            
        except Exception as e:
            logger.error(f"Error scraping {page_name}: {str(e)}")
            return False

    def _analyze_players_intelligently(self, soup: BeautifulSoup) -> bool:
        """Интелигентен анализ на играчите"""
        players_found = 0
        
        # Търсим таблици с играчи
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            
            if len(rows) < 2:
                continue
            
            # Анализираме хедърите
            header_row = rows[0]
            headers = [th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])]
            
            # Проверяваме дали това е таблица с играчи
            player_indicators = ['име', 'name', 'возраст', 'age', 'goa', 'def', 'att', 'sho', 'spe', 'str', 'pas']
            
            if not any(indicator in ' '.join(headers) for indicator in player_indicators):
                continue
            
            # Извличаме данните за играчите
            for row_idx, row in enumerate(rows[1:], 1):
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 3:
                    continue
                
                player_data = {
                    'source': 'players_analysis',
                    'table': table_idx + 1,
                    'row': row_idx,
                    'analyzed_at': datetime.now().isoformat()
                }
                
                # Картографираме данните
                for col_idx, cell in enumerate(cells):
                    if col_idx < len(headers):
                        cell_text = cell.get_text().strip()
                        if cell_text and cell_text not in ['-', '']:
                            player_data[headers[col_idx]] = cell_text
                
                # Добавяме интелигентен анализ
                if len(player_data) >= 5:
                    # Изчисляваме рейтинга
                    player_data['ai_rating'] = self.calculate_player_rating(player_data)
                    
                    # Определяме позицията
                    player_data['suggested_position'] = self._determine_best_position(player_data)
                    
                    # Възрастова категория
                    age = self._extract_age(player_data)
                    if age:
                        player_data['age_category'] = self._categorize_age(age)
                    
                    self.data['players'].append(player_data)
                    players_found += 1
        
        print(f"     🧮 AI Analysis: {players_found} players, avg rating calculated")
        return players_found > 0

    def _analyze_market_intelligently(self, soup: BeautifulSoup) -> bool:
        """Интелигентен анализ на трансферния пазар"""
        market_players = []
        
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            if len(rows) < 2:
                continue
                
            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            
            # Търсим маркет индикатори
            market_indicators = ['цена', 'price', 'оферта', 'bid', 'срок', 'deadline']
            
            if not any(indicator in ' '.join(headers) for indicator in market_indicators):
                continue
            
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 2:
                    continue
                
                market_data = {}
                
                for col_idx, cell in enumerate(cells):
                    if col_idx < len(headers):
                        cell_text = cell.get_text().strip()
                        if cell_text and cell_text not in ['-', '']:
                            market_data[headers[col_idx]] = cell_text
                
                if len(market_data) >= 2:
                    # Добавяме AI анализ
                    market_data['ai_analysis'] = self._analyze_market_player(market_data)
                    market_players.append(market_data)
        
        self.data['market_data'] = market_players
        
        # Генерираме transfer opportunities
        self.data['transfer_targets'] = self.analyze_market_opportunities()
        
        print(f"     📊 Market Analysis: {len(market_players)} players, {len(self.data['transfer_targets'])} opportunities found")
        return len(market_players) > 0

    def _analyze_market_player(self, player_data: Dict) -> Dict:
        """Анализира отделен играч от пазара"""
        analysis = {
            'value_assessment': 'unknown',
            'risk_level': 'medium',
            'recommendation': 'evaluate'
        }
        
        # Тук можем да добавим по-сложен анализ
        # засега връщаме основен анализ
        
        return analysis

    def _determine_best_position(self, player_data: Dict) -> str:
        """Определя най-добрата позиция за играч"""
        ratings = {}
        
        for position, weights in self.position_weights.items():
            ratings[position] = self.calculate_player_rating(player_data, position)
        
        best_position = max(ratings, key=ratings.get)
        return best_position

    def _extract_age(self, player_data: Dict) -> Optional[int]:
        """Извлича възрастта от данните на играча"""
        for key, value in player_data.items():
            if 'възраст' in key.lower() or 'age' in key.lower():
                age_match = re.search(r'\d+', str(value))
                if age_match:
                    return int(age_match.group())
        return None

    def _categorize_age(self, age: int) -> str:
        """Категоризира възрастта"""
        if age < 20:
            return 'junior'
        elif age < 25:
            return 'young'
        elif age < 30:
            return 'prime'
        elif age < 35:
            return 'veteran'
        else:
            return 'senior'

    def _analyze_youth_intelligently(self, soup: BeautifulSoup) -> bool:
        """Интелигентен анализ на младежката школа"""
        youth_players = []
        
        # Подобен подход като при основните играчи
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            if len(rows) < 2:
                continue
                
            headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
            
            # Младежки индикатори
            youth_indicators = ['талант', 'talent', 'потенциал', 'potential', 'качество', 'quality']
            
            if any(indicator in ' '.join(headers) for indicator in youth_indicators):
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 3:
                        youth_data = {}
                        
                        for col_idx, cell in enumerate(cells):
                            if col_idx < len(headers):
                                cell_text = cell.get_text().strip()
                                if cell_text and cell_text not in ['-', '']:
                                    youth_data[headers[col_idx]] = cell_text
                        
                        if len(youth_data) >= 3:
                            # AI анализ за младежи
                            youth_data['potential_rating'] = self._calculate_youth_potential(youth_data)
                            youth_data['development_time'] = self._estimate_development_time(youth_data)
                            youth_players.append(youth_data)
        
        self.data['youth_players'] = youth_players
        self.data['youth_school']['players'] = youth_players
        self.data['youth_school']['count'] = len(youth_players)
        
        print(f"     🌱 Youth Analysis: {len(youth_players)} prospects analyzed")
        return len(youth_players) > 0

    def _calculate_youth_potential(self, youth_data: Dict) -> float:
        """Изчислява потенциала на млад играч"""
        # Търсим качество и потенциал в данните
        quality = 50  # default
        potential = 50  # default
        
        for key, value in youth_data.items():
            if 'качество' in key.lower() or 'quality' in key.lower():
                numbers = re.findall(r'\d+', str(value))
                if numbers:
                    quality = int(numbers[0])
            elif 'потенциал' in key.lower() or 'potential' in key.lower():
                numbers = re.findall(r'\d+', str(value))
                if numbers:
                    potential = int(numbers[0])
        
        # Комбиниран скор
        return round((quality * 0.4 + potential * 0.6), 1)

    def _estimate_development_time(self, youth_data: Dict) -> str:
        """Оценява времето за развитие"""
        age = self._extract_age(youth_data)
        
        if age and age < 18:
            return "2-3 years"
        elif age and age < 20:
            return "1-2 years"
        else:
            return "6 months - 1 year"

    def _analyze_finances_intelligently(self, soup: BeautifulSoup) -> bool:
        """Интелигентен финансов анализ"""
        finances = {}
        
        # Търсим финансови данни
        text = soup.get_text()
        
        # Различни формати за пари
        money_patterns = [
            (r'(\d{1,3}(?:[\s,]\d{3})*)\s*(?:лв|лева|BGN)', 'BGN'),
            (r'(\d{1,3}(?:[\s,]\d{3})*)\s*(?:\$|USD|долара)', 'USD'),
            (r'(\d{1,3}(?:[\s,]\d{3})*)\s*(?:€|EUR|евро)', 'EUR'),
            (r'(\d+)\s*(?:милиона?|million)', 'millions')
        ]
        
        for pattern, currency in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                finances[f'amounts_{currency}'] = matches[:5]  # Първите 5
        
        # Търсим таблици с финансови данни
        tables = soup.find_all('table')
        financial_data = []
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    
                    if any(keyword in key.lower() for keyword in ['приход', 'разход', 'баланс', 'бюджет', 'income', 'expense']):
                        financial_data.append({'item': key, 'value': value})
        
        finances['financial_items'] = financial_data
        
        # AI финансов анализ
        finances['ai_analysis'] = self._analyze_financial_health(finances)
        
        self.data['finances'] = finances
        
        print(f"     💰 Financial Analysis: {len(financial_data)} items, health assessed")
        return len(finances) > 0

    def _analyze_financial_health(self, finances: Dict) -> Dict:
        """Анализира финансовото здраве"""
        analysis = {
            'health_status': 'unknown',
            'recommendations': [],
            'risk_factors': []
        }
        
        # Тук може да добавим по-сложен финансов анализ
        # засега връщаме основен анализ
        
        analysis['recommendations'].append("Следете редовно финансовите отчети")
        return analysis

    def _analyze_tactics_intelligently(self, soup: BeautifulSoup) -> bool:
        """Интелигентен тактически анализ"""
        tactics = {}
        
        # Търсим форми и select полета
        form_elements = soup.find_all(['input', 'select', 'option'])
        
        for element in form_elements:
            name = element.get('name', '')
            
            if any(keyword in name.lower() for keyword in ['tactic', 'formation', 'strategy', 'тактика']):
                if element.name == 'select':
                    selected = element.find('option', {'selected': True})
                    if selected:
                        tactics[name] = selected.get_text().strip()
                elif element.name == 'input':
                    value = element.get('value', '')
                    if value:
                        tactics[name] = value
        
        # AI тактически анализ
        tactics['ai_suggestions'] = self._generate_tactical_suggestions()
        
        self.data['tactics'] = tactics
        
        print(f"     ⚡ Tactical Analysis: {len(tactics)} settings, AI suggestions generated")
        return len(tactics) > 0

    def _generate_tactical_suggestions(self) -> List[str]:
        """Генерира тактически предложения"""
        suggestions = []
        
        team_analysis = self.analyze_team_strengths_weaknesses()
        
        # Базираме предложенията на анализа на отбора
        if 'Силна defenseman позиция' in ' '.join(team_analysis['strengths']):
            suggestions.append("🛡️ Използвайте оборонителна тактика")
        
        if 'Силна forward позиция' in ' '.join(team_analysis['strengths']):
            suggestions.append("⚔️ Играйте агресивно в атака")
        
        if team_analysis['age_analysis'].get('average_age', 25) > 30:
            suggestions.append("🔄 Ротирайте състава по-често")
        
        suggestions.append("📊 Анализирайте противника преди всеки мач")
        
        return suggestions

    def _generic_page_analysis(self, soup: BeautifulSoup, page_name: str) -> bool:
        """Общ анализ за останалите страници"""
        data = {
            'tables': len(soup.find_all('table')),
            'forms': len(soup.find_all('form')),
            'inputs': len(soup.find_all('input')),
            'analyzed_at': datetime.now().isoformat()
        }
        
        # Извличаме числа от страницата
        text = soup.get_text()
        numbers = re.findall(r'\d+', text)
        
        if numbers:
            data['numbers_found'] = len(numbers)
            data['sample_numbers'] = numbers[:10]  # Първите 10
        
        self.data[page_name] = data
        
        print(f"     📋 Generic Analysis: {data['tables']} tables, {data['forms']} forms")
        return True

    def perform_comprehensive_ai_analysis(self):
        """Извършва пълен AI анализ на всички данни"""
        print("\n🧠 Performing comprehensive AI analysis...")
        
        ai_analysis = {
            'timestamp': datetime.now().isoformat(),
            'team_analysis': self.analyze_team_strengths_weaknesses(),
            'transfer_opportunities': self.analyze_market_opportunities(),
            'training_plan': self.generate_training_plan(),
            'financial_health': self.data.get('finances', {}).get('ai_analysis', {}),
            'tactical_suggestions': self.data.get('tactics', {}).get('ai_suggestions', []),
            'overall_recommendations': []
        }
        
        # Генерираме общи препоръки
        recommendations = []
        
        team_analysis = ai_analysis['team_analysis']
        
        # Препоръки за играчи
        if team_analysis['overall_rating'] < 50:
            recommendations.append("🔄 Приоритет: Подобряване на качеството на отбора")
        
        if len(team_analysis['weaknesses']) > len(team_analysis['strengths']):
            recommendations.append("⚠️ Фокус върху слабите места в отбора")
        
        # Препоръки за възраст
        avg_age = team_analysis.get('age_analysis', {}).get('average_age', 25)
        if avg_age > 29:
            recommendations.append("👥 Инвестирайте в млади играчи")
        elif avg_age < 23:
            recommendations.append("🎓 Развивайте младите таланти")
        
        # Трансферни препоръки
        if len(ai_analysis['transfer_opportunities']) > 0:
            top_opportunity = ai_analysis['transfer_opportunities'][0]
            recommendations.append(f"💰 Разгледайте {top_opportunity['player']} (score: {top_opportunity['opportunity_score']})")
        
        ai_analysis['overall_recommendations'] = recommendations
        
        self.data['ai_analysis'] = ai_analysis
        
        print(f"     ✅ AI Analysis complete: {len(recommendations)} recommendations generated")

    def save_intelligent_results(self) -> Tuple[str, str, List[str]]:
        """Запазва резултатите с AI анализ"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON файл с пълни данни
        json_file = f"hockey_arena_intelligent_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        # Интелигентен отчет
        report_file = f"hockey_arena_ai_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🏒 HOCKEY ARENA AI ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"User: {self.username}\n\n")
            
            # AI анализ
            if 'ai_analysis' in self.data:
                ai = self.data['ai_analysis']
                
                f.write("🧠 AI TEAM ANALYSIS:\n")
                team_analysis = ai.get('team_analysis', {})
                f.write(f"  • Overall Rating: {team_analysis.get('overall_rating', 0)}/100\n")
                f.write(f"  • Average Age: {team_analysis.get('age_analysis', {}).get('average_age', 'N/A')}\n")
                
                f.write("\n💪 STRENGTHS:\n")
                for strength in team_analysis.get('strengths', []):
                    f.write(f"  • {strength}\n")
                
                f.write("\n⚠️ WEAKNESSES:\n")
                for weakness in team_analysis.get('weaknesses', []):
                    f.write(f"  • {weakness}\n")
                
                f.write("\n🎯 TRANSFER OPPORTUNITIES:\n")
                for i, opp in enumerate(ai.get('transfer_opportunities', [])[:5], 1):
                    f.write(f"  {i}. {opp['player']} - Score: {opp['opportunity_score']} ({opp['recommendation']})\n")
                
                f.write("\n🏃 TRAINING PLAN:\n")
                training_plan = ai.get('training_plan', {})
                for priority in training_plan.get('priorities', []):
                    f.write(f"  • {priority}\n")
                
                f.write("\n⚡ TACTICAL SUGGESTIONS:\n")
                for suggestion in ai.get('tactical_suggestions', []):
                    f.write(f"  • {suggestion}\n")
                
                f.write("\n🎯 OVERALL RECOMMENDATIONS:\n")
                for rec in ai.get('overall_recommendations', []):
                    f.write(f"  • {rec}\n")
        
        # CSV файлове
        csv_files = []
        
        # Играчи с AI анализ
        if self.data['players']:
            players_csv = f"players_ai_analysis_{timestamp}.csv"
            
            fieldnames = set()
            for player in self.data['players']:
                fieldnames.update(player.keys())
            
            with open(players_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(self.data['players'])
            csv_files.append(players_csv)
        
        # Трансферни възможности
        if self.data.get('transfer_opportunities'):
            transfer_csv = f"transfer_opportunities_{timestamp}.csv"
            
            with open(transfer_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['player', 'rating', 'price', 'age', 'value_ratio', 'opportunity_score', 'recommendation'])
                writer.writeheader()
                writer.writerows(self.data['transfer_opportunities'])
            csv_files.append(transfer_csv)
        
        print(f"\n💾 Intelligent Results saved:")
        print(f"   📄 {json_file} (complete AI analysis)")
        print(f"   📄 {report_file} (AI report)")
        for csv_file in csv_files:
            print(f"   📄 {csv_file} (structured data)")
        
        return json_file, report_file, csv_files

    def run_intelligent_analysis(self) -> bool:
        """Стартира интелигентния анализ"""
        print("🚀 Starting INTELLIGENT Hockey Arena Analysis...")
        print("🧠 AI-Powered with human-like behavior")
        print("=" * 60)
        
        # Логване
        if not self.login():
            print("❌ Login failed - stopping analysis")
            return False
        
        print("✅ Login successful! Starting intelligent scraping...")
        
        # Общ брой страници
        total_pages = sum(len(pages) for pages in self.analysis_pages.values())
        current_page = 0
        
        # Скрейпваме по приоритет
        for priority, pages in self.analysis_pages.items():
            print(f"\n📊 Analyzing {priority} pages...")
            
            for page_name, page_url in pages.items():
                current_page += 1
                print(f"🔍 [{current_page}/{total_pages}] {page_name}")
                
                success = self.scrape_page_intelligently(page_name, page_url)
                
                if not success and priority == 'critical':
                    print(f"⚠️ Critical page {page_name} failed - continuing anyway")
                
                # Human-like delay between pages
                self._human_delay(2.0, 5.0)
        
        print(f"\n🧠 Starting AI analysis of collected data...")
        
        # Извършваме AI анализ
        self.perform_comprehensive_ai_analysis()
        
        # Запазваме резултатите
        json_file, report_file, csv_files = self.save_intelligent_results()
        
        # Финален доклад
        print(f"\n🎉 INTELLIGENT ANALYSIS COMPLETED!")
        print(f"📈 Results:")
        print(f"   • Players analyzed: {len(self.data['players'])}")
        print(f"   • Market opportunities: {len(self.data.get('transfer_opportunities', []))}")
        print(f"   • Youth prospects: {len(self.data.get('youth_players', []))}")
        
        if 'ai_analysis' in self.data:
            ai = self.data['ai_analysis']
            print(f"   • Team rating: {ai.get('team_analysis', {}).get('overall_rating', 0)}/100")
            print(f"   • AI recommendations: {len(ai.get('overall_recommendations', []))}")
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Review the AI report: {report_file}")
        print(f"   2. Check transfer opportunities")
        print(f"   3. Implement training plan")
        print(f"   4. Apply tactical suggestions")
        
        return True

def main():
    print("🏒 HOCKEY ARENA INTELLIGENT ANALYZER v2.0")
    print("🧠 AI-Powered Analysis with Human-like Behavior")
    print("=" * 70)
    
    # Настройки - сложете вашите данни тук
    username = "delirium"
    password = "Zweider4e"
    
    analyzer = IntelligentHockeyAnalyzer(username, password)
    
    try:
        success = analyzer.run_intelligent_analysis()
        
        if success:
            print("\n✅ SUCCESS! Intelligent analysis completed.")
            print("🎯 Use the generated insights to dominate Hockey Arena!")
        else:
            print("\n❌ ANALYSIS FAILED!")
            
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        logger.error(f"Main execution error: {str(e)}")

if __name__ == "__main__":
    main()