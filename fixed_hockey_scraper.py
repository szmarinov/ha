#!/usr/bin/env python3
"""
Fixed Hockey Arena Scraper - Handling JavaScript redirects
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re
import csv

class FixedHockeyAnalyzer:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = "https://www.hockeyarena.net"
        
        self.data = {
            'team_info': {},
            'players': [],
            'matches': [],
            'standings': {},
            'finances': {},
            'tactics': {},
            'training': {},
            'youth_school': {},
            'stadium': {},
            'scouting': {},
            'market_data': [],
            'statistics': {},
            'calendar': [],
            'analysis': {}
        }
        
        # Headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'bg,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Cache-Control': 'no-cache'
        })
        
        # Страници за scraping
        self.pages_to_scrape = {
            'summary': 'manager_summary.php',
            'players': 'manager_team_players.php',
            'team_statistics': 'manager_team_statistics.php',
            'standings': 'public_standings.inc',
            'finances': 'manager_finance_report.inc',
            'tactics': 'manager_tactics_form.php',
            'training': 'manager_training_form1.php',
            'training_schedules': 'manager_training_schedules_form.php',
            'lineup': 'manager_lines_lineup_form_new.php',
            'youth_school': 'manager_youth_school_form.php',
            'scouting': 'manager_scouting_form.php',
            'market': 'manager_player_market_form.php',
            'calendar': 'manager_calendar.php',
            'news': 'manager_news.php',
            'stars': 'manager_stars_form.php',
            'jersey': 'manager_jersey.inc',
            'bonuses': 'manager_league_bonuses.php'
        }
        
        print(f"🏒 Fixed Hockey Arena Analyzer initialized")
        print(f"👤 User: {username}")

    def login(self):
        """Поправено логване с JavaScript redirect handling"""
        print("\n🔐 Attempting login...")
        
        try:
            # Стъпка 1: Вземаме login страницата
            login_url = f"{self.base_url}/bg/login"
            print(f"📄 Accessing: {login_url}")
            
            response = self.session.get(login_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Cannot access login page: {response.status_code}")
                return False
            
            # Стъпка 2: Подготвяме login данните (вече знаем структурата)
            login_data = {
                'nick': self.username,
                'password': self.password,
                'submit': 'Влез в играта'
            }
            
            print(f"📤 Posting login data...")
            
            # Стъпка 3: Изпращаме login заявката
            action_url = f"{self.base_url}/bg/index.php?p=security_log.php"
            login_response = self.session.post(action_url, data=login_data, allow_redirects=True)
            
            print(f"📨 Response: {login_response.status_code}")
            print(f"🔗 Final URL: {login_response.url}")
            
            # Стъпка 4: Проверяваме за JavaScript redirect
            response_text = login_response.text
            
            # Търсим JavaScript redirect
            js_redirect_match = re.search(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", response_text)
            
            if js_redirect_match:
                redirect_url = js_redirect_match.group(1)
                print(f"🔄 JavaScript redirect detected: {redirect_url}")
                
                # Следваме redirect-а
                if not redirect_url.startswith('http'):
                    redirect_url = f"{self.base_url}/bg/{redirect_url}"
                
                print(f"🔗 Following redirect to: {redirect_url}")
                redirect_response = self.session.get(redirect_url, timeout=15)
                
                print(f"📨 Redirect response: {redirect_response.status_code}")
                
                # Проверяваме дали сме в manager областта
                if redirect_response.status_code == 200:
                    content = redirect_response.text.lower()
                    
                    # Търсим индикатори за успешен login
                    manager_indicators = [
                        'manager_', 'logout', 'отбор', 'играчи', 'мачове', 
                        'стадион', 'тактики', 'team', 'players'
                    ]
                    
                    found_indicators = [ind for ind in manager_indicators if ind in content]
                    
                    if found_indicators:
                        print(f"✅ Login successful! Found indicators: {found_indicators[:3]}")
                        
                        # Запазваме успешната страница
                        with open('successful_login_page.html', 'w', encoding='utf-8') as f:
                            f.write(redirect_response.text)
                        
                        return True
            
            # Ако няма JavaScript redirect, проверяваме директно response-a
            content = login_response.text.lower()
            if any(indicator in content for indicator in ['manager_', 'logout', 'отбор']):
                print("✅ Login successful (direct)!")
                return True
            
            print("❌ Login failed - no manager area detected")
            
            # Запазваме за debug
            with open('login_debug_response.html', 'w', encoding='utf-8') as f:
                f.write(login_response.text)
            
            return False
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def scrape_page(self, page_name, page_url):
        """Scraping на конкретна страница"""
        print(f"\n📄 Scraping {page_name}...")
        
        try:
            full_url = f"{self.base_url}/bg/index.php?p={page_url}"
            response = self.session.get(full_url, timeout=15)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ Error: {response.status_code}")
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Запазваме страницата
            filename = f"{page_name}_page.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Анализираме според типа страница
            success = False
            
            if page_name == 'players':
                success = self.analyze_players_page(soup)
            elif page_name == 'team_statistics':
                success = self.analyze_statistics_page(soup)
            elif page_name == 'finances':
                success = self.analyze_finances_page(soup)
            elif page_name == 'tactics':
                success = self.analyze_tactics_page(soup)
            elif page_name == 'training':
                success = self.analyze_training_page(soup)
            elif page_name == 'youth_school':
                success = self.analyze_youth_school_page(soup)
            elif page_name == 'market':
                success = self.analyze_market_page(soup)
            elif page_name == 'news':
                success = self.analyze_news_page(soup)
            else:
                success = self.analyze_generic_page(soup, page_name)
            
            if success:
                print(f"   ✅ {page_name} analyzed successfully")
            else:
                print(f"   📄 {page_name} processed")
            
            return True
                
        except Exception as e:
            print(f"   ❌ Error scraping {page_name}: {e}")
            return False

    def analyze_players_page(self, soup):
        """Анализ на страницата с играчи"""
        print("   👥 Analyzing players...")
        
        players_found = 0
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            
            # Вземаме header row
            headers = []
            header_row = rows[0]
            for th in header_row.find_all(['th', 'td']):
                header_text = th.get_text().strip().lower()
                headers.append(header_text)
            
            # Проверяваме дали е таблица с играчи
            player_keywords = [
                'име', 'name', 'възраст', 'age', 'позиция', 'position',
                'вратар', 'goalie', 'защита', 'defense', 'атака', 'attack'
            ]
            
            matching_keywords = sum(1 for header in headers for keyword in player_keywords if keyword in header)
            
            if matching_keywords >= 2:  # Минимум 2 подходящи колони
                print(f"     📊 Player table found (table {table_idx+1}, {matching_keywords} matching columns)")
                
                # Извличаме данните за играчите
                for row_idx, row in enumerate(rows[1:], 1):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        player_data = {
                            'source': 'players_page',
                            'table': table_idx + 1,
                            'row': row_idx
                        }
                        
                        for col_idx, cell in enumerate(cells):
                            if col_idx < len(headers):
                                cell_text = cell.get_text().strip()
                                if cell_text and cell_text not in ['-', '']:
                                    player_data[headers[col_idx]] = cell_text
                        
                        if len(player_data) >= 5:  # Минимум 5 полета (включително meta)
                            self.data['players'].append(player_data)
                            players_found += 1
        
        print(f"     ✅ Found {players_found} players")
        return players_found > 0

    def analyze_statistics_page(self, soup):
        """Анализ на статистиките"""
        print("   📊 Analyzing team statistics...")
        
        stats = {}
        
        # Търсим таблици
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    if key and value and len(key) < 100:  # Разумна дължина
                        stats[key] = value
        
        # Търсим числа и статистики в текста
        text = soup.get_text()
        
        # Статистики за голове, мачове и т.н.
        stat_patterns = {
            'goals': r'(\d+)\s*(гол|goal)',
            'matches': r'(\d+)\s*(мач|match)',
            'wins': r'(\d+)\s*(победа|win)',
            'points': r'(\d+)\s*(точка|point)'
        }
        
        for stat_name, pattern in stat_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                stats[f'{stat_name}_found'] = [match[0] for match in matches[:3]]
        
        self.data['statistics'] = stats
        print(f"     ✅ Found {len(stats)} statistics")
        return len(stats) > 0

    def analyze_finances_page(self, soup):
        """Анализ на финансите"""
        print("   💰 Analyzing finances...")
        
        finances = {}
        
        # Търсим суми
        text = soup.get_text()
        
        # Различни формати за пари
        money_patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*[$€лв]',
            r'[$€]\s*(\d{1,3}(?:,\d{3})*)',
            r'(\d+)\s*милиона?',
            r'(\d+)\s*хиляди'
        ]
        
        all_amounts = []
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            all_amounts.extend(matches)
        
        if all_amounts:
            finances['amounts_found'] = all_amounts[:10]
        
        # Търсим финансови таблици
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) == 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    
                    # Финансови ключови думи
                    financial_keywords = [
                        'приход', 'разход', 'баланс', 'заплата', 'бюджет',
                        'income', 'expense', 'budget', 'salary', 'balance'
                    ]
                    
                    if any(keyword in key.lower() for keyword in financial_keywords):
                        finances[key] = value
        
        self.data['finances'] = finances
        print(f"     ✅ Found financial data")
        return len(finances) > 0

    def analyze_tactics_page(self, soup):
        """Анализ на тактиките"""
        print("   ⚽ Analyzing tactics...")
        
        tactics = {}
        
        # Input полета
        inputs = soup.find_all('input')
        for inp in inputs:
            name = inp.get('name', '')
            value = inp.get('value', '')
            input_type = inp.get('type', '')
            
            if name and value and input_type in ['number', 'text', 'hidden']:
                tactics[name] = value
        
        # Select полета
        selects = soup.find_all('select')
        for select in selects:
            name = select.get('name', '')
            selected_option = select.find('option', {'selected': True})
            if name and selected_option:
                tactics[name] = selected_option.get_text().strip()
        
        self.data['tactics'] = tactics
        print(f"     ✅ Found {len(tactics)} tactical settings")
        return len(tactics) > 0

    def analyze_training_page(self, soup):
        """Анализ на тренировките"""
        print("   🏃 Analyzing training...")
        
        training = {}
        
        # Търсим всички input и select полета
        form_elements = soup.find_all(['input', 'select'])
        for element in form_elements:
            name = element.get('name', '')
            if 'train' in name.lower() or 'form' in name.lower():
                if element.name == 'select':
                    selected = element.find('option', {'selected': True})
                    if selected:
                        training[name] = selected.get_text().strip()
                else:
                    value = element.get('value', '')
                    if value:
                        training[name] = value
        
        # Търсим тренировъчни таблици
        tables = soup.find_all('table')
        training_data = []
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 1:
                headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
                
                if any(keyword in ' '.join(headers) for keyword in ['train', 'тренировка', 'form', 'condition']):
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            row_data = [cell.get_text().strip() for cell in cells]
                            training_data.append(row_data)
        
        if training_data:
            training['training_table'] = training_data[:5]  # Първите 5 реда
        
        self.data['training'] = training
        print(f"     ✅ Found training data")
        return len(training) > 0

    def analyze_youth_school_page(self, soup):
        """Анализ на юношеската школа"""
        print("   👶 Analyzing youth school...")
        
        youth_players = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 1:
                headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
                
                # Проверяваме дали е таблица с млади играчи
                if any(keyword in ' '.join(headers) for keyword in ['име', 'name', 'възраст', 'age']):
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            player_data = {}
                            for i, cell in enumerate(cells):
                                if i < len(headers):
                                    player_data[headers[i]] = cell.get_text().strip()
                            
                            if player_data:
                                youth_players.append(player_data)
        
        self.data['youth_school'] = {
            'players': youth_players,
            'count': len(youth_players)
        }
        
        print(f"     ✅ Found {len(youth_players)} youth players")
        return len(youth_players) > 0

    def analyze_market_page(self, soup):
        """Анализ на трансферния пазар"""
        print("   🏪 Analyzing transfer market...")
        
        market_players = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 1:
                headers = [th.get_text().strip().lower() for th in rows[0].find_all(['th', 'td'])]
                
                # Проверяваме дали е пазарна таблица
                market_keywords = ['име', 'name', 'цена', 'price', 'оферта', 'bid']
                if any(keyword in ' '.join(headers) for keyword in market_keywords):
                    
                    for row in rows[1:10]:  # Първите 10 играча
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            player_data = {}
                            for i, cell in enumerate(cells):
                                if i < len(headers):
                                    player_data[headers[i]] = cell.get_text().strip()
                            
                            if player_data:
                                market_players.append(player_data)
        
        self.data['market_data'] = market_players
        print(f"     ✅ Found {len(market_players)} market players")
        return len(market_players) > 0

    def analyze_news_page(self, soup):
        """Анализ на новините"""
        print("   📰 Analyzing news...")
        
        news_items = []
        
        # Търсим новини в различни формати
        news_containers = soup.find_all(['div', 'p', 'tr'])
        
        for container in news_containers:
            text = container.get_text().strip()
            if len(text) > 50 and len(text) < 500:  # Разумна дължина за новина
                # Търсим дати в текста
                date_match = re.search(r'\d{1,2}[./]\d{1,2}[./]\d{2,4}', text)
                
                news_item = {
                    'text': text[:200],  # Първите 200 символа
                    'date': date_match.group(0) if date_match else 'Unknown'
                }
                news_items.append(news_item)
                
                if len(news_items) >= 10:  # Максимум 10 новини
                    break
        
        self.data['news'] = news_items
        print(f"     ✅ Found {len(news_items)} news items")
        return len(news_items) > 0

    def analyze_generic_page(self, soup, page_name):
        """Общ анализ на страници"""
        print(f"     📄 Generic analysis of {page_name}...")
        
        # Основна статистика
        tables_count = len(soup.find_all('table'))
        forms_count = len(soup.find_all('form'))
        inputs_count = len(soup.find_all('input'))
        
        # Търсим числа в текста
        text = soup.get_text()
        numbers = re.findall(r'\d+', text)
        
        generic_data = {
            'tables': tables_count,
            'forms': forms_count,
            'inputs': inputs_count,
            'numbers_found': len(numbers),
            'sample_numbers': numbers[:10] if numbers else []
        }
        
        # Запазваме в data според page_name
        if page_name not in self.data:
            self.data[page_name] = {}
        self.data[page_name].update(generic_data)
        
        print(f"     📊 Tables: {tables_count}, Forms: {forms_count}, Inputs: {inputs_count}")
        return True

    def comprehensive_analysis(self):
        """Пълен анализ на събраните данни"""
        print(f"\n🧠 Performing comprehensive analysis...")
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'insights': [],
            'recommendations': []
        }
        
        # Анализ на играчите
        total_players = len(self.data['players'])
        analysis['summary']['total_players'] = total_players
        
        if total_players > 0:
            # Позиции
            positions = {}
            ages = []
            
            for player in self.data['players']:
                for key, value in player.items():
                    if 'позиция' in key.lower() or 'position' in key.lower():
                        positions[value] = positions.get(value, 0) + 1
                    
                    if 'възраст' in key.lower() or 'age' in key.lower():
                        try:
                            age_match = re.search(r'\d+', str(value))
                            if age_match:
                                age = int(age_match.group())
                                if 15 <= age <= 45:  # Разумни граници за възраст
                                    ages.append(age)
                        except:
                            pass
            
            analysis['summary']['positions'] = positions
            if ages:
                analysis['summary']['average_age'] = round(sum(ages) / len(ages), 1)
                analysis['summary']['age_range'] = f"{min(ages)}-{max(ages)}"
        
        # Анализ на другите категории
        categories = ['finances', 'tactics', 'youth_school', 'market_data', 'statistics', 'training']
        
        for category in categories:
            if category in self.data and self.data[category]:
                if isinstance(self.data[category], dict):
                    if category == 'youth_school':
                        analysis['summary'][f'{category}_count'] = self.data[category].get('count', 0)
                    else:
                        analysis['summary'][f'{category}_items'] = len(self.data[category])
                elif isinstance(self.data[category], list):
                    analysis['summary'][f'{category}_count'] = len(self.data[category])
        
        # Генериране на insights и препоръки
        if total_players > 0:
            analysis['insights'].append(f"Отборът има {total_players} играчи в базата данни")
        
        if analysis['summary'].get('average_age', 0) > 28:
            analysis['recommendations'].append("Средната възраст е висока - помислете за млади играчи")
        
        if analysis['summary'].get('youth_school_count', 0) < 5:
            analysis['recommendations'].append("Малко играчи в юношеската школа - инвестирайте в развитие")
        
        if analysis['summary'].get('market_data_count', 0) > 0:
            analysis['insights'].append(f"Намерени {analysis['summary']['market_data_count']} играчи на пазара")
        
        self.data['analysis'] = analysis
        return analysis

    def save_comprehensive_results(self):
        """Запазване на всички резултати"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON файл
        json_file = f"hockey_arena_fixed_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        # CSV файлове
        csv_files = []
        
        if self.data['players']:
            players_csv = f"players_fixed_{timestamp}.csv"
            # Събираме всички възможни колони
            all_keys = set()
            for player in self.data['players']:
                all_keys.update(player.keys())
            
            with open(players_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(self.data['players'])
            csv_files.append(players_csv)
        
        if self.data['market_data']:
            market_csv = f"market_fixed_{timestamp}.csv"
            all_keys = set()
            for player in self.data['market_data']:
                all_keys.update(player.keys())
            
            with open(market_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(self.data['market_data'])
            csv_files.append(market_csv)
        
        # Подробен отчет
        report_file = f"hockey_arena_fixed_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🏒 HOCKEY ARENA COMPREHENSIVE ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"User: {self.username}\n\n")
            
            if 'analysis' in self.data:
                analysis = self.data['analysis']
                
                f.write("📊 SUMMARY:\n")
                for key, value in analysis.get('summary', {}).items():
                    f.write(f"  • {key}: {value}\n")
                
                f.write("\n🔍 INSIGHTS:\n")
                for insight in analysis.get('insights', []):
                    f.write(f"  • {insight}\n")
                
                f.write("\n💡 RECOMMENDATIONS:\n")
                for rec in analysis.get('recommendations', []):
                    f.write(f"  • {rec}\n")
            
            # Детайли по категории
            categories_to_show = ['players', 'market_data', 'finances', 'tactics', 'youth_school']
            
            for category in categories_to_show:
                if self.data.get(category):
                    f.write(f"\n📋 {category.upper()}:\n")
                    
                    if isinstance(self.data[category], list):
                        f.write(f"  Count: {len(self.data[category])}\n")
                        for i, item in enumerate(self.data[category][:3], 1):
                            f.write(f"  {i}. {str(item)[:100]}...\n")
                        if len(self.data[category]) > 3:
                            f.write(f"  ... and {len(self.data[category]) - 3} more\n")
                    
                    elif isinstance(self.data[category], dict):
                        for key, value in list(self.data[category].items())[:5]:
                            f.write(f"  {key}: {str(value)[:50]}\n")
                        if len(self.data[category]) > 5:
                            f.write(f"  ... and {len(self.data[category]) - 5} more\n")
        
        print(f"\n💾 Results saved:")
        print(f"   📄 {json_file} (complete data)")
        print(f"   📄 {report_file} (readable report)")
        for csv_file in csv_files:
            print(f"   📄 {csv_file} (CSV data)")
        
        return json_file, report_file, csv_files

    def run_comprehensive_analysis(self):
        """Стартиране на пълния анализ"""
        print("🚀 Starting FIXED comprehensive Hockey Arena analysis...")
        print(f"🎯 Target: {len(self.pages_to_scrape)} pages")
        
        # Логване
        if not self.login():
            print("❌ Login failed - stopping analysis")
            return False
        
        print("✅ Login successful!")
        time.sleep(2)
        
        # Scraping на всички страници
        success_count = 0
        failed_pages = []
        
        for page_name, page_url in self.pages_to_scrape.items():
            if self.scrape_page(page_name, page_url):
                success_count += 1
            else:
                failed_pages.append(page_name)
            time.sleep(2)  # Пауза между заявките
        
        print(f"\n📊 Scraping completed:")
        print(f"   ✅ Successful: {success_count}/{len(self.pages_to_scrape)} pages")
        if failed_pages:
            print(f"   ❌ Failed: {failed_pages}")
        
        # Comprehensive анализ
        analysis = self.comprehensive_analysis()
        
        # Запазване на резултатите
        json_file, report_file, csv_files = self.save_comprehensive_results()
        
        print(f"\n🎉 COMPREHENSIVE ANALYSIS COMPLETED!")
        print(f"📈 Results:")
        print(f"   • Players found: {len(self.data['players'])}")
        print(f"   • Market players: {len(self.data['market_data'])}")
        print(f"   • Youth players: {self.data['youth_school'].get('count', 0)}")
        print(f"   • Financial data items: {len(self.data['finances'])}")
        print(f"   • Tactical settings: {len(self.data['tactics'])}")
        print(f"   • Training data: {len(self.data['training'])}")
        print(f"   • Statistics: {len(self.data['statistics'])}")
        
        return True

def main():
    print("🏒 FIXED COMPREHENSIVE HOCKEY ARENA ANALYZER")
    print("=" * 55)
    
    username = "delirium"
    password = "Zweider4e"
    
    analyzer = FixedHockeyAnalyzer(username, password)
    success = analyzer.run_comprehensive_analysis()
    
    if success:
        print("\n✅ SUCCESS! Complete Hockey Arena analysis finished.")
        print("📁 Check all the generated files for comprehensive data.")
        print("\n🎯 Next step: Use this data to create the perfect Hockey Arena Organizer!")
    else:
        print("\n❌ ANALYSIS FAILED!")

if __name__ == "__main__":
    main()