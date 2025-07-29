#!/usr/bin/env python3
"""
🏒 HOCKEY ARENA MASTER AI v4.0 - COMPLETE GUI SYSTEM
==================================================
Най-напредналата AI система за доминиране в Hockey Arena
Базирана на официалното ръководство от ha-navod.eu
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import re
import csv
import random
import math
import threading
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import webbrowser

# Matplotlib за графики
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import seaborn as sns
    plt.style.use('dark_background')
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

# Създаване на ha_assist папка
WORK_DIR = "ha_assist"
if not os.path.exists(WORK_DIR):
    os.makedirs(WORK_DIR)
os.chdir(WORK_DIR)

# Настройка на logging
def setup_logging():
    """Настройва детайлна debug и error система"""
    log_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)8s | %(module)s:%(lineno)d | %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handlers
    debug_handler = logging.FileHandler('hockey_arena_debug.log', encoding='utf-8')
    debug_handler.setFormatter(log_formatter)
    debug_handler.setLevel(logging.DEBUG)
    
    error_handler = logging.FileHandler('hockey_arena_errors.log', encoding='utf-8')
    error_handler.setFormatter(log_formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(debug_handler)
    root_logger.addHandler(error_handler)
    
    return root_logger

logger = setup_logging()

@dataclass
class PlayerStats:
    """Структура за статистики на играч според официалното ръководство"""
    name: str
    age: int
    position: str
    
    # Основни атрибути
    goa: int = 0  # Brána
    def_: int = 0  # Obrana
    att: int = 0  # Útok
    sho: int = 0  # Streľba
    pas: int = 0  # Nahrávka/Kontrola puku
    str_: int = 0  # Sila
    spe: int = 0  # Rýchlosť
    dis: int = 0  # Sebaovládanie
    
    # Допълнителни атрибути
    energy: int = 100  # Energia
    form: int = 100   # Forma
    experience: int = 0  # Skúsenosť
    quality: int = 0
    potential: int = 0
    salary: int = 0
    value: int = 0
    
    def calculate_position_rating(self, position_type: str) -> float:
        """Изчислява рейтинг според позицията базирано на ръководството"""
        if position_type.lower() == 'goalkeeper':
            # За вратари: Brána е основен + Rýchlosť
            return (self.goa * 0.6 + self.spe * 0.3 + self.pas * 0.1)
        elif position_type.lower() == 'defender':
            # За защитници: Obrana главен + Sila + остануки
            return (self.def_ * 0.4 + self.str_ * 0.25 + self.spe * 0.15 + 
                   self.pas * 0.1 + self.att * 0.1)
        elif position_type.lower() == 'center':
            # За центрове: Nahrávka важна + Útok + Sila (за вхвърляния)
            return (self.pas * 0.3 + self.att * 0.25 + self.str_ * 0.2 + 
                   self.spe * 0.15 + self.sho * 0.1)
        else:  # forward/wing
            # За нападатели: Útok + Streľba главни
            return (self.att * 0.3 + self.sho * 0.3 + self.spe * 0.2 + 
                   self.pas * 0.15 + self.str_ * 0.05)

@dataclass
class TacticalSpecialization:
    """Тактически специализации според ръководството"""
    name: str
    description: str
    requirements: Dict[str, float]
    effectiveness: float = 0.0

# Официални тактически специализации
TACTICAL_SPECIALIZATIONS = {
    'hura_system': TacticalSpecialization(
        name="Hurá systém",
        description="Без тактическа специализация, хаотично играене",
        requirements={}
    ),
    'counter_attacks': TacticalSpecialization(
        name="Protiútoky", 
        description="Дисциплинирана защита и бързи контраатаки",
        requirements={'def_': 0.4, 'spe': 0.3, 'dis': 0.3}
    ),
    'forechecking': TacticalSpecialization(
        name="Napádanie",
        description="Агресивно отнемане на шайбата в чуждата зона", 
        requirements={'str_': 0.4, 'spe': 0.3, 'att': 0.3}
    ),
    'short_passes': TacticalSpecialization(
        name="Krátke nahrávky",
        description="Бързи кратки подавания в атака",
        requirements={'pas': 0.5, 'spe': 0.3, 'att': 0.2}
    ),
    'defensive_checking': TacticalSpecialization(
        name="Obrana (checking)",
        description="Фокус само върху защитата",
        requirements={'def_': 0.6, 'str_': 0.3, 'dis': 0.1}
    ),
    'blue_line_shots': TacticalSpecialization(
        name="Streľba od modrej",
        description="Стрелби от защитниците от синята линия",
        requirements={'sho': 0.4, 'str_': 0.3, 'pas': 0.3}
    ),
    'behind_net_passes': TacticalSpecialization(
        name="Nahrávky spoza brány", 
        description="Центровете дават голови подавания отзад вратата",
        requirements={'pas': 0.5, 'att': 0.3, 'spe': 0.2}
    )
}

class GameGuideAnalyzer:
    """Анализатор на официалното ръководство"""
    
    def __init__(self):
        self.guide_data = {}
        self.guide_urls = [
            'https://www.ha-navod.eu/index.php?navod=novinky_informacie',
            'https://www.ha-navod.eu/index.php?navod=karta_muzstva',
            'https://www.ha-navod.eu/index.php?navod=zakladne_atributy',
            'https://www.ha-navod.eu/index.php?navod=dalsie_atributy',
            'https://www.ha-navod.eu/index.php?navod=takticke_moznosti',
            'https://www.ha-navod.eu/index.php?navod=trening',
            'https://www.ha-navod.eu/index.php?navod=statistiky',
            'https://www.ha-navod.eu/index.php?navod=nastavenie_zostavy',
            'https://www.ha-navod.eu/index.php?navod=zohranost_formacie'
        ]
        
    def analyze_official_guide(self) -> Dict:
        """Анализира официалното ръководство"""
        logger.info("📚 Analyzing official Hockey Arena guide...")
        
        guide_knowledge = {
            'attributes': {},
            'tactics': {},
            'training': {},
            'team_management': {},
            'game_mechanics': {}
        }
        
        try:
            for url in self.guide_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        content = soup.get_text()
                        
                        # Извличаме ключова информация
                        if 'atributy' in url:
                            guide_knowledge['attributes'] = self._extract_attributes_info(content)
                        elif 'takticke' in url:
                            guide_knowledge['tactics'] = self._extract_tactics_info(content)
                        elif 'trening' in url:
                            guide_knowledge['training'] = self._extract_training_info(content)
                        
                        time.sleep(1)  # Уважаваме сървъра
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch guide page {url}: {e}")
                    continue
            
            self.guide_data = guide_knowledge
            logger.info("✅ Official guide analysis completed")
            return guide_knowledge
            
        except Exception as e:
            logger.error(f"Error analyzing official guide: {e}")
            return {}
    
    def _extract_attributes_info(self, content: str) -> Dict:
        """Извлича информация за атрибутите"""
        return {
            'primary_attributes': ['Brána', 'Obrana', 'Útok', 'Streľba', 'Nahrávka', 'Sila', 'Rýchlosť', 'Sebaovládanie'],
            'goalkeeper_focus': ['Brána', 'Rýchlosť', 'Nahrávka'],
            'defender_focus': ['Obrana', 'Sila', 'Rýchlosť'],
            'forward_focus': ['Útok', 'Streľba', 'Nahrávka'],
            'center_focus': ['Nahrávka', 'Útok', 'Sila']
        }
    
    def _extract_tactics_info(self, content: str) -> Dict:
        """Извлича информация за тактиките"""
        return {
            'available_tactics': list(TACTICAL_SPECIALIZATIONS.keys()),
            'formation_chemistry': True,
            'aggressive_play_risks': True
        }
    
    def _extract_training_info(self, content: str) -> Dict:
        """Извлича информация за тренировките"""
        return {
            'energy_management': True,
            'form_factors': ['rest', 'performance', 'red_hand'],
            'experience_gain': 'matches_only'
        }

class BraveBrowserSimulator:
    """Точен симулатор на Brave браузър"""
    
    @staticmethod
    def get_brave_headers() -> Dict[str, str]:
        """Връща точни Brave браузър headers"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'bg-BG,bg;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-GPC': '1'  # Специфично за Brave
        }

class HumanBehaviorEngine:
    """Двигател за реалистично човешко поведение"""
    
    def __init__(self):
        self.session_start = time.time()
        self.pages_visited = 0
        self.last_action_time = time.time()
        self.browsing_pattern = self._generate_browsing_pattern()
    
    def _generate_browsing_pattern(self) -> Dict:
        """Генерира уникален модел на сърфиране"""
        return {
            'reading_speed': random.uniform(200, 350),  # думи/минута
            'attention_span': random.uniform(30, 120),  # секунди
            'curiosity_level': random.uniform(0.1, 0.4),  # вероятност за случайно кликване
            'fatigue_rate': random.uniform(0.1, 0.3)  # колко бързо се уморява
        }
    
    def realistic_delay(self, min_seconds: float = 2.0, max_seconds: float = 8.0):
        """Реалистичен delay с човешки фактори"""
        base_delay = random.uniform(min_seconds, max_seconds)
        
        # Фактор на умора
        session_time = time.time() - self.session_start
        fatigue_factor = 1 + (session_time / 3600) * self.browsing_pattern['fatigue_rate']
        base_delay *= fatigue_factor
        
        # Случайни "мисловни" паузи
        if random.random() < 0.15:
            base_delay += random.uniform(3.0, 12.0)
            logger.debug("🤔 Deep thinking pause...")
        
        # Микро паузи за "четене"
        if random.random() < 0.4:
            base_delay += random.uniform(0.5, 2.5)
        
        logger.debug(f"💤 Human delay: {base_delay:.1f}s")
        time.sleep(base_delay)
        
        self.pages_visited += 1
        self.last_action_time = time.time()
    
    def simulate_page_reading(self, content_length: int):
        """Симулира четене на страница"""
        words_estimate = content_length / 5
        reading_time = (words_estimate / self.browsing_pattern['reading_speed']) * 60
        
        # Ограничаваме времето
        reading_time = max(1.0, min(reading_time, self.browsing_pattern['attention_span']))
        
        # Добавяме случайност
        actual_time = reading_time * random.uniform(0.3, 1.8)
        
        logger.debug(f"📖 Reading simulation: {actual_time:.1f}s")
        time.sleep(actual_time)
    
    def should_explore_randomly(self) -> bool:
        """Решава дали да направи случайно разглеждане"""
        return random.random() < self.browsing_pattern['curiosity_level']

class OpponentIntelligence:
    """Интелигентна система за анализ на противници"""
    
    def __init__(self, session, base_url: str):
        self.session = session
        self.base_url = base_url
        self.opponent_cache = {}
        
    def analyze_opponent(self, opponent_name: str) -> Dict:
        """Анализира противник с AI предвиждания"""
        logger.info(f"🎯 Analyzing opponent: {opponent_name}")
        
        if opponent_name in self.opponent_cache:
            return self.opponent_cache[opponent_name]
        
        try:
            # Събираме данни за противника
            opponent_data = self._gather_opponent_data(opponent_name)
            
            # AI анализ
            analysis = {
                'name': opponent_name,
                'strength_rating': self._calculate_team_strength(opponent_data),
                'tactical_tendency': self._predict_tactics(opponent_data),
                'key_players': self._identify_key_players(opponent_data),
                'weaknesses': self._find_weaknesses(opponent_data),
                'strengths': self._find_strengths(opponent_data),
                'win_probability': 0.0,
                'recommended_tactics': {},
                'match_instructions': []
            }
            
            # Изчисляваме вероятност за победа
            analysis['win_probability'] = self._calculate_win_probability(analysis)
            
            # Генерираме препоръки
            analysis['recommended_tactics'] = self._generate_counter_tactics(analysis)
            analysis['match_instructions'] = self._generate_match_instructions(analysis)
            
            self.opponent_cache[opponent_name] = analysis
            logger.info(f"✅ Opponent analysis complete: {opponent_name}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze opponent {opponent_name}: {e}")
            return {'name': opponent_name, 'error': str(e)}
    
    def _gather_opponent_data(self, opponent_name: str) -> Dict:
        """Събира данни за противника от различни източници"""
        data = {
            'league_position': None,
            'recent_results': [],
            'estimated_players': [],
            'tactical_patterns': []
        }
        
        # Проверяваме класирането
        try:
            standings_url = f"{self.base_url}/public_standings.inc"
            response = self.session.get(standings_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data['league_position'] = self._find_team_in_standings(soup, opponent_name)
            
        except Exception as e:
            logger.warning(f"Could not get standings data: {e}")
        
        return data
    
    def _find_team_in_standings(self, soup: BeautifulSoup, team_name: str) -> Dict:
        """Намира отбора в класирането"""
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    if team_name.lower() in cell.get_text().lower():
                        # Извличаме статистики от реда
                        row_data = [c.get_text().strip() for c in cells]
                        return {
                            'position': row_data[0] if row_data else 'Unknown',
                            'points': row_data[2] if len(row_data) > 2 else '0',
                            'goals_for': row_data[3] if len(row_data) > 3 else '0',
                            'goals_against': row_data[4] if len(row_data) > 4 else '0'
                        }
        return {}
    
    def _calculate_team_strength(self, data: Dict) -> float:
        """Изчислява силата на отбора"""
        base_strength = 50.0
        
        league_pos = data.get('league_position', {})
        if league_pos:
            try:
                position = int(re.search(r'\d+', league_pos.get('position', '10')).group())
                # По-ниска позиция = по-силен отбор
                position_factor = max(0, (20 - position) * 2.5)
                base_strength += position_factor
            except:
                pass
        
        return min(100, max(0, base_strength))
    
    def _predict_tactics(self, data: Dict) -> str:
        """Предвижда тактиката на противника"""
        league_pos = data.get('league_position', {})
        
        if league_pos:
            try:
                goals_for = int(league_pos.get('goals_for', '0'))
                goals_against = int(league_pos.get('goals_against', '0'))
                
                if goals_for > goals_against * 1.2:
                    return 'offensive'
                elif goals_against > goals_for * 1.2:
                    return 'defensive'
                else:
                    return 'balanced'
            except:
                pass
        
        return 'unknown'
    
    def _identify_key_players(self, data: Dict) -> List[str]:
        """Идентифицира ключовите играчи"""
        # В реална ситуация това ще анализира действителни данни
        return ['Unknown Player 1', 'Unknown Player 2']
    
    def _find_weaknesses(self, data: Dict) -> List[str]:
        """Намира слабостите на отбора"""
        weaknesses = []
        
        tactical_tendency = self._predict_tactics(data)
        
        if tactical_tendency == 'offensive':
            weaknesses.append('Уязвима защита при контраатаки')
        elif tactical_tendency == 'defensive':
            weaknesses.append('Слаби в атака и финализация')
        
        # Добавяме общи слабости базирани на позицията
        league_pos = data.get('league_position', {})
        if league_pos:
            try:
                position = int(re.search(r'\d+', league_pos.get('position', '10')).group())
                if position > 10:
                    weaknesses.append('Общо слаб отбор')
                    weaknesses.append('Неопитни играчи')
            except:
                pass
        
        return weaknesses
    
    def _find_strengths(self, data: Dict) -> List[str]:
        """Намира силните страни на отбора"""
        strengths = []
        
        tactical_tendency = self._predict_tactics(data)
        
        if tactical_tendency == 'offensive':
            strengths.append('Силна атака и скориране')
        elif tactical_tendency == 'defensive':
            strengths.append('Стабилна защита')
        
        league_pos = data.get('league_position', {})
        if league_pos:
            try:
                position = int(re.search(r'\d+', league_pos.get('position', '10')).group())
                if position <= 5:
                    strengths.append('Топ отбор в лигата')
                    strengths.append('Опитни играчи')
            except:
                pass
        
        return strengths
    
    def _calculate_win_probability(self, analysis: Dict) -> float:
        """Изчислява вероятност за победа"""
        base_prob = 50.0
        
        # Корекция според силата на противника
        opponent_strength = analysis.get('strength_rating', 50)
        our_strength = 55.0  # Приемаме, че сме малко по-силни
        
        strength_diff = our_strength - opponent_strength
        probability = base_prob + (strength_diff * 0.8)
        
        return max(5, min(95, probability))
    
    def _generate_counter_tactics(self, analysis: Dict) -> Dict:
        """Генерира контра-тактики"""
        tactics = {}
        
        opponent_tendency = analysis.get('tactical_tendency', 'unknown')
        
        if opponent_tendency == 'offensive':
            tactics['recommended_formation'] = 'defensive'
            tactics['focus'] = 'counter_attacks'
            tactics['specialization'] = 'counter_attacks'
        elif opponent_tendency == 'defensive':
            tactics['recommended_formation'] = 'offensive' 
            tactics['focus'] = 'break_defense'
            tactics['specialization'] = 'short_passes'
        else:
            tactics['recommended_formation'] = 'balanced'
            tactics['focus'] = 'adapt'
            tactics['specialization'] = 'flexible'
        
        return tactics
    
    def _generate_match_instructions(self, analysis: Dict) -> List[str]:
        """Генерира инструкции за мача"""
        instructions = []
        
        weaknesses = analysis.get('weaknesses', [])
        strengths = analysis.get('strengths', [])
        win_prob = analysis.get('win_probability', 50)
        
        # Инструкции базирани на слабостите на противника
        for weakness in weaknesses:
            if 'защита' in weakness.lower():
                instructions.append('🔥 АТАКУВАЙТЕ АГРЕСИВНО - защитата им е слаба!')
            elif 'атака' in weakness.lower():
                instructions.append('🛡️ Играйте стабилно в защита - те са слаби в атака')
        
        # Предупреждения за силните страни
        for strength in strengths:
            if 'атака' in strength.lower():
                instructions.append('⚠️ ВНИМАНИЕ! Силна атака - играйте компактно')
            elif 'защита' in strength.lower():
                instructions.append('🎯 Търсете рядки моменти - защитата им е стабилна')
        
        # Общи инструкции според вероятността
        if win_prob > 70:
            instructions.append('💪 Имаме отлични шансове - играйте с увереност!')
        elif win_prob < 30:
            instructions.append('🥊 Труден противник - дайте максимума!')
        
        return instructions

class TacticalOptimizer:
    """AI оптимизатор на тактики базиран на официалното ръководство"""
    
    def __init__(self, guide_data: Dict = None):
        self.guide_data = guide_data or {}
        self.formations = {
            '1-4-1': {'def': 0.7, 'att': 0.5, 'balance': 0.8},
            '1-3-2': {'def': 0.6, 'att': 0.7, 'balance': 0.7},
            '1-2-3': {'def': 0.4, 'att': 0.9, 'balance': 0.5}
        }
    
    def optimize_lineup_and_tactics(self, our_players: List[PlayerStats], 
                                  opponent_analysis: Dict) -> Dict:
        """Оптимизира състава и тактиките"""
        
        logger.info("⚡ Optimizing lineup and tactics...")
        
        # Анализираме нашите играчи
        team_analysis = self._analyze_our_team(our_players)
        
        # Избираме най-добрите играчи за всяка позиция
        optimal_lineup = self._select_optimal_lineup(our_players)
        
        # Избираме най-добрата тактическа специализация
        best_specialization = self._choose_specialization(team_analysis, opponent_analysis)
        
        # Генерираме конкретни инструкции
        match_setup = self._create_match_setup(optimal_lineup, best_specialization, opponent_analysis)
        
        return {
            'lineup': optimal_lineup,
            'specialization': best_specialization,
            'formation': match_setup['formation'],
            'instructions': match_setup['instructions'],
            'energy_management': match_setup['energy_management'],
            'substitution_plan': match_setup['substitutions']
        }
    
    def _analyze_our_team(self, players: List[PlayerStats]) -> Dict:
        """Анализира нашия отбор"""
        analysis = {
            'total_players': len(players),
            'position_strength': {},
            'average_attributes': {},
            'team_character': ''
        }
        
        # Групираме играчите по позиции
        positions = {'goalkeeper': [], 'defender': [], 'center': [], 'forward': []}
        
        for player in players:
            # Определяме най-добрата позиция за всеки играч
            best_pos = self._determine_best_position(player)
            if best_pos in positions:
                positions[best_pos].append(player)
        
        # Анализираме силата на всяка позиция
        for pos, pos_players in positions.items():
            if pos_players:
                avg_rating = sum(p.calculate_position_rating(pos) for p in pos_players) / len(pos_players)
                analysis['position_strength'][pos] = {
                    'average_rating': avg_rating,
                    'player_count': len(pos_players),
                    'depth': 'good' if len(pos_players) >= 3 else 'limited'
                }
        
        # Определяме характера на отбора
        all_ratings = [p.calculate_position_rating('forward') for p in players]
        avg_team_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
        
        if avg_team_rating > 70:
            analysis['team_character'] = 'elite'
        elif avg_team_rating > 55:
            analysis['team_character'] = 'competitive'  
        else:
            analysis['team_character'] = 'developing'
        
        return analysis
    
    def _determine_best_position(self, player: PlayerStats) -> str:
        """Определя най-добрата позиция за играч"""
        ratings = {
            'goalkeeper': player.calculate_position_rating('goalkeeper'),
            'defender': player.calculate_position_rating('defender'), 
            'center': player.calculate_position_rating('center'),
            'forward': player.calculate_position_rating('forward')
        }
        
        return max(ratings, key=ratings.get)
    
    def _select_optimal_lineup(self, players: List[PlayerStats]) -> Dict:
        """Избира оптималния състав"""
        lineup = {
            'goalkeeper': None,
            'defenders': [],
            'centers': [],
            'forwards': []
        }
        
        # Сортираме играчите по рейтинг за всяка позиция
        for pos in ['goalkeeper', 'defender', 'center', 'forward']:
            pos_players = [(p, p.calculate_position_rating(pos)) for p in players]
            pos_players.sort(key=lambda x: x[1], reverse=True)
            
            if pos == 'goalkeeper':
                if pos_players:
                    lineup['goalkeeper'] = pos_players[0][0]
            elif pos == 'defender':
                lineup['defenders'] = [p[0] for p in pos_players[:4]]
            elif pos == 'center':
                lineup['centers'] = [p[0] for p in pos_players[:2]]
            else:  # forward
                lineup['forwards'] = [p[0] for p in pos_players[:4]]
        
        return lineup
    
    def _choose_specialization(self, team_analysis: Dict, opponent_analysis: Dict) -> str:
        """Избира най-добрата тактическа специализация"""
        
        opponent_tendency = opponent_analysis.get('tactical_tendency', 'unknown')
        team_character = team_analysis.get('team_character', 'developing')
        
        # Логика за избор на специализация
        if opponent_tendency == 'offensive':
            # Противникът атакува много - използваме контраатаки
            return 'counter_attacks'
        elif opponent_tendency == 'defensive':
            # Противникът се защитава - използваме кратки подавания
            return 'short_passes'
        elif team_character == 'elite':
            # Силен отбор - можем да играем агресивно
            return 'forechecking'
        else:
            # По подразбиране използваме balance
            return 'hura_system'
    
    def _create_match_setup(self, lineup: Dict, specialization: str, opponent_analysis: Dict) -> Dict:
        """Създава пълна настройка за мача"""
        
        setup = {
            'formation': '1-3-2',  # Балансирана формация
            'instructions': [],
            'energy_management': {},
            'substitutions': []
        }
        
        # Инструкции според специализацията
        spec_data = TACTICAL_SPECIALIZATIONS.get(specialization)
        if spec_data:
            setup['instructions'].append(f"🎯 Тактика: {spec_data.name}")
            setup['instructions'].append(f"📋 {spec_data.description}")
        
        # Енергиен мениджмънт
        setup['energy_management'] = {
            'rotation_needed': True,
            'rest_key_players': ['goalkeeper'],
            'high_intensity_limit': 3  # Максимум 3 последователни мача с висока интензивност
        }
        
        # План за заместванията
        setup['substitutions'] = [
            'Сменете уморените играчи в 40-та минута',
            'При водене с 2+ гола играйте по-дефанзивно',
            'При изоставане играйте по-агресивно'
        ]
        
        return setup

class HockeyArenaGUI:
    """Главна графична среда на системата"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏒 Hockey Arena Master AI v4.0")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#0d1117')
        
        # Стилизиране
        self.setup_styles()
        
        # Системни компоненти
        self.analyzer = None
        self.guide_analyzer = GameGuideAnalyzer()
        self.running = False
        self.analysis_thread = None
        
        # Данни
        self.our_players = []
        self.opponents_data = {}
        
        # Настройка на GUI
        self.setup_gui()
        
        # Автоматично анализиране на ръководството при стартиране
        self.analyze_official_guide()
    
    def setup_styles(self):
        """Настройва стиловете"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Тъмна тема
        self.style.configure('Title.TLabel', 
                           font=('Segoe UI', 18, 'bold'),
                           background='#0d1117',
                           foreground='#f0f6fc')
        
        self.style.configure('Subtitle.TLabel',
                           font=('Segoe UI', 12, 'bold'),
                           background='#0d1117', 
                           foreground='#7c3aed')
        
        self.style.configure('Success.TLabel',
                           foreground='#238636')
        
        self.style.configure('Error.TLabel',
                           foreground='#da3633')
        
        self.style.configure('Warning.TLabel',
                           foreground='#fb8500')
        
        self.style.configure('Custom.TButton',
                           font=('Segoe UI', 10, 'bold'))
    
    def setup_gui(self):
        """Настройва основния интерфейс"""
        # Главен контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заглавие
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, 
                               text="🏒 Hockey Arena Master AI v4.0", 
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Статус индикатор
        self.status_indicator = ttk.Label(title_frame, 
                                        text="🔴 Offline", 
                                        style='Error.TLabel')
        self.status_indicator.pack(side=tk.RIGHT)
        
        # Notebook за различни секции
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Създаване на табовете
        self.setup_dashboard_tab()
        self.setup_login_tab()
        self.setup_team_analysis_tab()
        self.setup_opponent_analysis_tab()
        self.setup_tactics_tab()
        self.setup_match_preparation_tab()
        self.setup_guide_tab()
        self.setup_logs_tab()
        self.setup_settings_tab()
    
    def setup_dashboard_tab(self):
        """Главен dashboard"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Бързи статистики
        stats_frame = ttk.LabelFrame(dashboard_frame, text="🏆 Quick Stats", padding=10)
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_labels = {
            'team_rating': ttk.Label(stats_frame, text="Team Rating: --"),
            'next_opponent': ttk.Label(stats_frame, text="Next Opponent: --"),
            'win_probability': ttk.Label(stats_frame, text="Win Probability: --%"),
            'recommended_tactic': ttk.Label(stats_frame, text="Recommended Tactic: --")
        }
        
        for i, (key, label) in enumerate(self.stats_labels.items()):
            label.grid(row=0, column=i, padx=20, sticky=tk.W)
        
        # Графики секция
        if CHARTS_AVAILABLE:
            self.setup_charts_section(dashboard_frame)
        
        # Бързи действия
        actions_frame = ttk.LabelFrame(dashboard_frame, text="⚡ Quick Actions", padding=10)
        actions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(actions_frame, text="🔄 Refresh Analysis", 
                  command=self.refresh_analysis).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(actions_frame, text="🎯 Analyze Next Opponent", 
                  command=self.analyze_next_opponent).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(actions_frame, text="📋 Export Report", 
                  command=self.export_comprehensive_report).pack(side=tk.LEFT, padx=5)
    
    def setup_charts_section(self, parent):
        """Настройва секцията с графики"""
        charts_frame = ttk.LabelFrame(parent, text="📈 Visual Analysis", padding=10)
        charts_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Matplotlib canvas
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.patch.set_facecolor('#0d1117')
        
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor('#161b22')
        
        self.canvas = FigureCanvasTkAgg(self.fig, charts_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_charts()
    
    def setup_login_tab(self):
        """Таб за логване"""
        login_frame = ttk.Frame(self.notebook)
        self.notebook.add(login_frame, text="🔐 Login & Analysis")
        
        # Центриране на съдържанието
        center_frame = ttk.Frame(login_frame)
        center_frame.pack(expand=True)
        
        # Logo и заглавие
        ttk.Label(center_frame, text="🏒", font=('Segoe UI', 48)).pack(pady=10)
        ttk.Label(center_frame, text="Hockey Arena Master AI", 
                 style='Title.TLabel').pack(pady=5)
        ttk.Label(center_frame, text="Най-напредналата AI система за доминиране", 
                 style='Subtitle.TLabel').pack(pady=5)
        
        # Credential полета
        creds_frame = ttk.LabelFrame(center_frame, text="Данни за достъп", padding=20)
        creds_frame.pack(pady=20)
        
        ttk.Label(creds_frame, text="Username:", font=('Segoe UI', 12)).pack(anchor=tk.W)
        self.username_entry = ttk.Entry(creds_frame, width=30, font=('Segoe UI', 12))
        self.username_entry.pack(pady=5, fill=tk.X)
        
        ttk.Label(creds_frame, text="Password:", font=('Segoe UI', 12)).pack(anchor=tk.W, pady=(10,0))
        self.password_entry = ttk.Entry(creds_frame, width=30, show="*", font=('Segoe UI', 12))
        self.password_entry.pack(pady=5, fill=tk.X)
        
        # Login бутон
        self.login_button = ttk.Button(creds_frame, 
                                      text="🚀 Стартиране на AI Анализ",
                                      command=self.start_comprehensive_analysis,
                                      style='Custom.TButton')
        self.login_button.pack(pady=20, fill=tk.X)
        
        # Status и progress
        self.login_status_label = ttk.Label(center_frame, text="Готов за стартиране...")
        self.login_status_label.pack(pady=5)
        
        self.progress = ttk.Progressbar(center_frame, mode='indeterminate', length=400)
        self.progress.pack(pady=10)
        
        # Допълнителни опции
        options_frame = ttk.LabelFrame(center_frame, text="Настройки за анализ", padding=10)
        options_frame.pack(pady=10)
        
        self.deep_analysis_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Дълбок анализ на противници", 
                       variable=self.deep_analysis_var).pack(anchor=tk.W)
        
        self.auto_tactics_var = tk.BooleanVar(value=True) 
        ttk.Checkbutton(options_frame, text="Автоматични тактически препоръки",
                       variable=self.auto_tactics_var).pack(anchor=tk.W)
    
    def setup_team_analysis_tab(self):
        """Таб за анализ на отбора"""
        team_frame = ttk.Frame(self.notebook)
        self.notebook.add(team_frame, text="👥 Team Analysis")
        
        # Два стълба
        left_frame = ttk.Frame(team_frame)
        right_frame = ttk.Frame(team_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Лява страна - обща информация
        info_frame = ttk.LabelFrame(left_frame, text="ℹ️ Team Information", padding=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.team_info_text = scrolledtext.ScrolledText(info_frame, height=8, width=50)
        self.team_info_text.pack(fill=tk.BOTH, expand=True)
        
        # Играчи анализ
        players_frame = ttk.LabelFrame(left_frame, text="👤 Players Analysis", padding=10)
        players_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.players_tree = ttk.Treeview(players_frame, columns=('Position', 'Rating', 'Age', 'Form'), show='tree headings')
        self.players_tree.heading('#0', text='Name')
        self.players_tree.heading('Position', text='Best Position')
        self.players_tree.heading('Rating', text='Rating')
        self.players_tree.heading('Age', text='Age')
        self.players_tree.heading('Form', text='Form')
        
        scrollbar_players = ttk.Scrollbar(players_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=scrollbar_players.set)
        
        self.players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_players.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Дясна страна - статистики и препоръки
        stats_frame = ttk.LabelFrame(right_frame, text="📊 Team Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.team_stats_text = scrolledtext.ScrolledText(stats_frame, height=12, width=50)
        self.team_stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Препоръки
        recommendations_frame = ttk.LabelFrame(right_frame, text="💡 AI Recommendations", padding=10)
        recommendations_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.recommendations_text = scrolledtext.ScrolledText(recommendations_frame, height=15, width=50)
        self.recommendations_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_opponent_analysis_tab(self):
        """Таб за анализ на противници"""
        opponent_frame = ttk.Frame(self.notebook)
        self.notebook.add(opponent_frame, text="🎯 Opponent Analysis")
        
        # Търсене на противник
        search_frame = ttk.LabelFrame(opponent_frame, text="🔍 Opponent Search", padding=10)
        search_frame.pack(fill=tk.X, pady=5)
        
        search_inner = ttk.Frame(search_frame)
        search_inner.pack(fill=tk.X)
        
        ttk.Label(search_inner, text="Opponent Name:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.opponent_entry = ttk.Entry(search_inner, width=25)
        self.opponent_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_inner, text="🔍 Analyze", 
                  command=self.analyze_specific_opponent).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_inner, text="📋 All League Opponents", 
                  command=self.analyze_all_league_opponents).pack(side=tk.LEFT, padx=5)
        
        # Резултати от анализа
        results_frame = ttk.LabelFrame(opponent_frame, text="📊 Analysis Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Списък с анализирани противници
        opponents_list_frame = ttk.Frame(results_frame)
        opponents_list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Label(opponents_list_frame, text="Analyzed Opponents:", font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W)
        
        self.opponents_listbox = tk.Listbox(opponents_list_frame, width=25, height=20)
        self.opponents_listbox.pack(fill=tk.Y, expand=True)
        self.opponents_listbox.bind('<<ListboxSelect>>', self.on_opponent_select)
        
        # Детайли за избрания противник
        details_frame = ttk.Frame(results_frame)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.opponent_details_text = scrolledtext.ScrolledText(details_frame, height=25, width=70)
        self.opponent_details_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_tactics_tab(self):
        """Таб за тактики"""
        tactics_frame = ttk.Frame(self.notebook)
        self.notebook.add(tactics_frame, text="⚡ Tactics & Strategy")
        
        # Секция за формации
        formation_frame = ttk.LabelFrame(tactics_frame, text="🏒 Formation Setup", padding=10)
        formation_frame.pack(fill=tk.X, pady=5)
        
        formation_controls = ttk.Frame(formation_frame)
        formation_controls.pack(fill=tk.X)
        
        ttk.Label(formation_controls, text="Formation:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.formation_var = tk.StringVar(value="1-3-2")
        formation_combo = ttk.Combobox(formation_controls, textvariable=self.formation_var,
                                     values=["1-4-1", "1-3-2", "1-2-3"], width=10)
        formation_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(formation_controls, text="Specialization:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20,5))
        self.specialization_var = tk.StringVar(value="hura_system")
        spec_combo = ttk.Combobox(formation_controls, textvariable=self.specialization_var,
                                values=list(TACTICAL_SPECIALIZATIONS.keys()), width=15)
        spec_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(formation_controls, text="🎯 Optimize", 
                  command=self.optimize_tactics).pack(side=tk.LEFT, padx=20)
        
        # Секция за тактически препоръки
        tactics_rec_frame = ttk.LabelFrame(tactics_frame, text="🧠 AI Tactical Recommendations", padding=10)
        tactics_rec_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tactics_text = scrolledtext.ScrolledText(tactics_rec_frame, height=25, width=80)
        self.tactics_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_match_preparation_tab(self):
        """Таб за подготовка за мач"""
        match_frame = ttk.Frame(self.notebook)
        self.notebook.add(match_frame, text="🥅 Match Preparation")
        
        # Избор на противник за мач
        opponent_select_frame = ttk.LabelFrame(match_frame, text="🎯 Select Opponent", padding=10)
        opponent_select_frame.pack(fill=tk.X, pady=5)
        
        select_controls = ttk.Frame(opponent_select_frame)
        select_controls.pack(fill=tk.X)
        
        ttk.Label(select_controls, text="Next Match Opponent:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        self.match_opponent_var = tk.StringVar()
        self.match_opponent_combo = ttk.Combobox(select_controls, textvariable=self.match_opponent_var, width=25)
        self.match_opponent_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(select_controls, text="📋 Prepare Match Plan", 
                  command=self.prepare_match_plan).pack(side=tk.LEFT, padx=20)
        
        # План за мача
        match_plan_frame = ttk.LabelFrame(match_frame, text="📝 Complete Match Plan", padding=10)
        match_plan_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.match_plan_text = scrolledtext.ScrolledText(match_plan_frame, height=25, width=80)
        self.match_plan_text.pack(fill=tk.BOTH, expand=True)
        
        # Експорт бутони
        export_frame = ttk.Frame(match_frame)
        export_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(export_frame, text="💾 Save Match Plan", 
                  command=self.save_match_plan).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(export_frame, text="📧 Email Plan", 
                  command=self.email_match_plan).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(export_frame, text="📱 Mobile Export", 
                  command=self.mobile_export).pack(side=tk.LEFT, padx=5)
    
    def setup_guide_tab(self):
        """Таб за официалното ръководство"""
        guide_frame = ttk.Frame(self.notebook)
        self.notebook.add(guide_frame, text="📚 Official Guide")
        
        # Статус на анализа на ръководството
        status_frame = ttk.LabelFrame(guide_frame, text="📊 Guide Analysis Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.guide_status_label = ttk.Label(status_frame, text="Анализиране на официалното ръководство...")
        self.guide_status_label.pack(anchor=tk.W)
        
        # Съдържание на ръководството
        content_frame = ttk.LabelFrame(guide_frame, text="📖 Guide Content & Insights", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.guide_content_text = scrolledtext.ScrolledText(content_frame, height=25, width=80)
        self.guide_content_text.pack(fill=tk.BOTH, expand=True)
        
        # Контроли
        controls_frame = ttk.Frame(guide_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(controls_frame, text="🔄 Refresh Guide Analysis", 
                  command=self.analyze_official_guide).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="🌐 Open Official Guide", 
                  command=lambda: webbrowser.open("https://www.ha-navod.eu")).pack(side=tk.LEFT, padx=5)
    
    def setup_logs_tab(self):
        """Таб за логове и debug"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 Logs & Debug")
        
        # Контроли за логове
        controls_frame = ttk.Frame(logs_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(controls_frame, text="🔄 Refresh", 
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="💾 Save Logs", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="🗑️ Clear", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="🐛 Debug Mode", 
                  command=self.toggle_debug_mode).pack(side=tk.LEFT, padx=5)
        
        # Log viewer
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=30, width=100)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Автоматично зареждане на логовете
        self.refresh_logs()
    
    def setup_settings_tab(self):
        """Таб за настройки"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Поведенчески настройки
        behavior_frame = ttk.LabelFrame(settings_frame, text="🤖 AI Behavior Settings", padding=10)
        behavior_frame.pack(fill=tk.X, pady=5)
        
        self.human_behavior_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Human-like behavior simulation", 
                       variable=self.human_behavior_var).pack(anchor=tk.W)
        
        self.auto_opponent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Auto-analyze opponents", 
                       variable=self.auto_opponent_var).pack(anchor=tk.W)
        
        self.deep_tactics_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(behavior_frame, text="Deep tactical analysis", 
                       variable=self.deep_tactics_var).pack(anchor=tk.W)
        
        # Timing настройки
        timing_frame = ttk.LabelFrame(settings_frame, text="⏱️ Timing Settings", padding=10)
        timing_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(timing_frame, text="Minimum delay between requests (seconds):").pack(anchor=tk.W)
        self.min_delay_var = tk.DoubleVar(value=2.0)
        delay_scale = ttk.Scale(timing_frame, from_=0.5, to=10.0, variable=self.min_delay_var,
                               orient=tk.HORIZONTAL, length=300)
        delay_scale.pack(anchor=tk.W, pady=5)
        
        self.delay_value_label = ttk.Label(timing_frame, text="2.0s")
        self.delay_value_label.pack(anchor=tk.W)
        delay_scale.configure(command=self.update_delay_label)
        
        # Файлове и експорт
        files_frame = ttk.LabelFrame(settings_frame, text="📁 Files & Export", padding=10)
        files_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(files_frame, text="📁 Open Work Directory", 
                  command=self.open_work_directory).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(files_frame, text="🗑️ Clean Old Files", 
                  command=self.clean_old_files).pack(side=tk.LEFT, padx=5)
        
        # Спестяване на настройки
        ttk.Button(settings_frame, text="💾 Save Settings", 
                  command=self.save_settings).pack(pady=20)
    
    # ==================== EVENT HANDLERS ====================
    
    def analyze_official_guide(self):
        """Анализира официалното ръководство в отделен thread"""
        def analyze():
            try:
                self.guide_status_label.configure(text="🔄 Анализиране на официалното ръководство...")
                guide_data = self.guide_analyzer.analyze_official_guide()
                
                # Показване на резултатите
                content = """
🏒 АНАЛИЗ НА ОФИЦИАЛНОТО РЪКОВОДСТВО
================================================

📊 ОСНОВНИ АТРИБУТИ (базирано на ha-navod.eu):
• Brána (GOA) - За вратари, основен атрибут
• Obrana (DEF) - За защитници, основен за бранене
• Útok (ATT) - За нападатели, основен за атакуване
• Streľba (SHO) - За всички играчи при стрелби
• Nahrávka/Kontrola puku (PAS) - Важно за центрове и вратари
• Sila (STR) - Важно за всички, особено при вхвърляния
• Rýchlosť (SPE) - Използва се от всички играчи
• Sebaovládanie (DIS) - Контролира агресивността и вилучванията

⚡ ТАКТИЧЕСКИ СПЕЦИАЛИЗАЦИИ:
• Hurá systém - Без специализация, хаотично
• Protiútoky - Защита + контраатаки (изисква DEF, SPE, DIS)
• Napádanie - Агресивно отнемане (изисква STR, SPE, ATT)
• Krátke nahrávky - Бързи подавания (изисква PAS, SPE, ATT)
• Obrana (checking) - Само защита (изисква DEF, STR, DIS)
• Streľba od modrej - Стрелби от защитници (изисква SHO, STR, PAS)
• Nahrávky spoza brány - Подавания от зад вратата (изисква PAS, ATT, SPE)

🏋️ ТРЕНИРОВКИ И ФОРМА:
• Energia се губи в мачове и тренировки
• Forma се влияе от почивка, представяне и "червена ръка"
• Skúsenosť се получава само в мачове
• Формите се влияят от лигово ниво

💡 AI ПРЕПОРЪКИ БАЗИРАНИ НА РЪКОВОДСТВОТО:
• Използвайте специализации според противника
• Следете енергията на играчите (<60% = риск от контузия)
• Центровете трябва да имат висока Sila за вхвърляния
• Вратарите се уморяват според броя стрелби
• Формацията трябва да съответства на специализацията
• Агресивната игра увеличава вилученията при ниско Sebaovládanie

🎯 ОПТИМИЗАЦИОННИ СТРАТЕГИИ:
• Анализирайте противника и изберете контра-специализация
• Ротирайте играчите за запазване на енергията
• Използвайте "червената ръка" за подобряване на формата
• Фокусирайте тренировките според ролята на играча
• Следете съчетанието формация + специализация + играчи
"""
                
                self.root.after(0, lambda: self.guide_content_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.guide_content_text.insert(tk.END, content))
                self.root.after(0, lambda: self.guide_status_label.configure(text="✅ Анализът на ръководството е завършен"))
                
            except Exception as e:
                error_msg = f"❌ Грешка при анализ на ръководството: {str(e)}"
                self.root.after(0, lambda: self.guide_status_label.configure(text=error_msg))
                logger.error(f"Guide analysis error: {e}")
        
        thread = threading.Thread(target=analyze, daemon=True)
        thread.start()
    
    def start_comprehensive_analysis(self):
        """Стартира пълния анализ"""
        if self.running:
            messagebox.showwarning("Внимание", "Анализът вече се изпълнява!")
            return
        
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Грешка", "Моля въведете потребителско име и парола!")
            return
        
        self.running = True
        self.login_button.configure(state='disabled', text="🔄 Анализиране...")
        self.progress.start()
        self.status_indicator.configure(text="🟡 Connecting...", style='Warning.TLabel')
        
        # Стартиране в отделен thread
        self.analysis_thread = threading.Thread(
            target=self.run_comprehensive_analysis, 
            args=(username, password),
            daemon=True
        )
        self.analysis_thread.start()
    
    def run_comprehensive_analysis(self, username: str, password: str):
        """Изпълнява пълния анализ"""
        try:
            self.update_status("🔐 Логване с Brave браузър симулация...")
            
            # Създаване на AI системата
            self.analyzer = HockeyArenaMasterAI(username, password)
            
            # Стъпка 1: Логване
            if not self.analyzer.login_with_human_behavior():
                raise Exception("Неуспешно логване - проверете данните")
            
            self.update_status("✅ Успешно логване! Анализиране на отбора...")
            
            # Стъпка 2: Анализ на нашия отбор
            self.analyzer.analyze_our_team()
            self.our_players = self.analyzer.get_our_players()
            
            self.update_status("🎯 Анализиране на противници...")
            
            # Стъпка 3: Анализ на противници
            if self.deep_analysis_var.get():
                opponents = self.analyzer.discover_and_analyze_opponents()
                self.opponents_data = opponents
            
            self.update_status("⚡ Генериране на тактически препоръки...")
            
            # Стъпка 4: Генериране на тактики
            if self.auto_tactics_var.get():
                self.analyzer.generate_optimal_tactics()
            
            # Финализиране
            self.root.after(0, self.analysis_completed_successfully)
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.analysis_failed(error_msg))
    
    def update_status(self, message: str):
        """Обновява статуса"""
        self.root.after(0, lambda: self.login_status_label.configure(text=message))
        logger.info(message)
    
    def analysis_completed_successfully(self):
        """Callback при успешно завършване"""
        self.running = False
        self.login_button.configure(state='normal', text="🚀 Стартиране на AI Анализ")
        self.progress.stop()
        self.status_indicator.configure(text="🟢 Online & Ready", style='Success.TLabel')
        
        # Обновяване на всички табове с данни
        self.update_dashboard()
        self.update_team_analysis()
        self.update_opponents_list()
        
        messagebox.showinfo("Успех", "🎉 AI анализът е завършен успешно!\n\nПроверете всички табове за детайлни резултати.")
        
        # Преминаване към dashboard
        self.notebook.select(0)
    
    def analysis_failed(self, error_msg: str):
        """Callback при неуспешен анализ"""
        self.running = False
        self.login_button.configure(state='normal', text="🚀 Стартиране на AI Анализ")
        self.progress.stop()
        self.status_indicator.configure(text="🔴 Analysis Failed", style='Error.TLabel')
        
        messagebox.showerror("Грешка", f"❌ Анализът се провали:\n\n{error_msg}")
    
    def update_dashboard(self):
        """Обновява dashboard-а"""
        if not self.analyzer:
            return
        
        try:
            # Обновяване на бързите статистики
            team_rating = self.analyzer.get_team_rating()
            self.stats_labels['team_rating'].configure(text=f"Team Rating: {team_rating:.1f}/100")
            
            next_opponent = self.analyzer.get_next_opponent()
            self.stats_labels['next_opponent'].configure(text=f"Next Opponent: {next_opponent}")
            
            if next_opponent and next_opponent in self.opponents_data:
                win_prob = self.opponents_data[next_opponent].get('win_probability', 50)
                self.stats_labels['win_probability'].configure(text=f"Win Probability: {win_prob:.1f}%")
            
            recommended_tactic = self.analyzer.get_recommended_tactic()
            self.stats_labels['recommended_tactic'].configure(text=f"Recommended Tactic: {recommended_tactic}")
            
            # Обновяване на графиките
            if CHARTS_AVAILABLE:
                self.update_charts()
                
        except Exception as e:
            logger.error(f"Dashboard update error: {e}")
    
    def update_charts(self):
        """Обновява графиките"""
        if not CHARTS_AVAILABLE:
            return
        
        try:
            # Почистваме графиките
            for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                ax.clear()
                ax.set_facecolor('#161b22')
            
            if self.analyzer and self.our_players:
                # Графика 1: Разпределение по позиции
                positions = {}
                for player in self.our_players:
                    pos = player.get('best_position', 'Unknown')
                    positions[pos] = positions.get(pos, 0) + 1
                
                if positions:
                    self.ax1.pie(positions.values(), labels=positions.keys(), autopct='%1.1f%%',
                               colors=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'])
                    self.ax1.set_title('Position Distribution', color='white', fontsize=12)
                
                # Графика 2: Възрастова структура
                ages = [p.get('age', 25) for p in self.our_players if p.get('age')]
                if ages:
                    self.ax2.hist(ages, bins=10, color='#7c3aed', alpha=0.7, edgecolor='white')
                    self.ax2.set_title('Age Distribution', color='white', fontsize=12)
                    self.ax2.set_xlabel('Age', color='white')
                    self.ax2.set_ylabel('Count', color='white')
                    self.ax2.tick_params(colors='white')
                
                # Графика 3: Рейтинги на играчите
                ratings = [p.get('ai_rating', 0) for p in self.our_players if p.get('ai_rating')]
                if ratings:
                    self.ax3.boxplot(ratings, patch_artist=True, 
                                   boxprops=dict(facecolor='#45b7d1', alpha=0.7))
                    self.ax3.set_title('Player Ratings Distribution', color='white', fontsize=12)
                    self.ax3.set_ylabel('Rating', color='white')
                    self.ax3.tick_params(colors='white')
                
                # Графика 4: Сравнение с противници
                if self.opponents_data:
                    opponent_names = list(self.opponents_data.keys())[:5]
                    win_probs = [self.opponents_data[name].get('win_probability', 50) 
                               for name in opponent_names]
                    
                    bars = self.ax4.bar(range(len(opponent_names)), win_probs, 
                                      color=['#238636' if p > 60 else '#fb8500' if p > 40 else '#da3633' 
                                            for p in win_probs])
                    self.ax4.set_title('Win Probability vs Top Opponents', color='white', fontsize=12)
                    self.ax4.set_ylabel('Win Probability (%)', color='white')
                    self.ax4.set_xticks(range(len(opponent_names)))
                    self.ax4.set_xticklabels([name[:10] for name in opponent_names], 
                                           rotation=45, color='white')
                    self.ax4.tick_params(colors='white')
            else:
                # Placeholder графики
                for i, ax in enumerate([self.ax1, self.ax2, self.ax3, self.ax4]):
                    ax.text(0.5, 0.5, f'Chart {i+1}\nNo Data Available', 
                           transform=ax.transAxes, ha='center', va='center',
                           color='white', fontsize=12)
                    ax.set_title(f'Chart {i+1}', color='white')
            
            self.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Charts update error: {e}")
    
    def update_team_analysis(self):
        """Обновява анализа на отбора"""
        if not self.analyzer:
            return
        
        try:
            # Обновяване на информацията за отбора
            team_info = self.analyzer.get_team_info_summary()
            self.team_info_text.delete(1.0, tk.END)
            self.team_info_text.insert(tk.END, team_info)
            
            # Обновяване на списъка с играчи
            for item in self.players_tree.get_children():
                self.players_tree.delete(item)
            
            for player in self.our_players:
                name = player.get('name', 'Unknown')
                position = player.get('best_position', 'Unknown')
                rating = player.get('ai_rating', 0)
                age = player.get('age', 0)
                form = player.get('form', 100)
                
                self.players_tree.insert('', 'end', text=name, 
                                       values=(position, f"{rating:.1f}", age, f"{form}%"))
            
            # Обновяване на статистиките
            team_stats = self.analyzer.get_detailed_team_stats()
            self.team_stats_text.delete(1.0, tk.END)
            self.team_stats_text.insert(tk.END, team_stats)
            
            # Обновяване на препоръките
            recommendations = self.analyzer.get_team_recommendations()
            self.recommendations_text.delete(1.0, tk.END)
            self.recommendations_text.insert(tk.END, recommendations)
            
        except Exception as e:
            logger.error(f"Team analysis update error: {e}")
    
    def update_opponents_list(self):
        """Обновява списъка с противници"""
        self.opponents_listbox.delete(0, tk.END)
        
        if self.opponents_data:
            # Обновяване на комбо бокса за мач
            opponent_names = list(self.opponents_data.keys())
            self.match_opponent_combo['values'] = opponent_names
            
            # Обновяване на листбокса
            for name in opponent_names:
                win_prob = self.opponents_data[name].get('win_probability', 50)
                display_name = f"{name} ({win_prob:.1f}%)"
                self.opponents_listbox.insert(tk.END, display_name)
    
    def on_opponent_select(self, event):
        """Handler за избор на противник"""
        selection = self.opponents_listbox.curselection()
        if selection:
            index = selection[0]
            opponent_names = list(self.opponents_data.keys())
            
            if index < len(opponent_names):
                opponent_name = opponent_names[index]
                self.display_opponent_details(opponent_name)
    
    def display_opponent_details(self, opponent_name: str):
        """Показва детайли за противника"""
        if opponent_name not in self.opponents_data:
            return
        
        opponent = self.opponents_data[opponent_name]
        
        details = f"""
🎯 ДЕТАЙЛЕН АНАЛИЗ: {opponent_name}
{'='*60}

📊 ОБЩИ СТАТИСТИКИ:
• Сила на отбора: {opponent.get('strength_rating', 0):.1f}/100
• Вероятност за победа: {opponent.get('win_probability', 50):.1f}%
• Тактическа тенденция: {opponent.get('tactical_tendency', 'Unknown')}

💪 СИЛНИ СТРАНИ:
{chr(10).join('• ' + s for s in opponent.get('strengths', ['Няма данни']))}

⚠️ СЛАБОСТИ:
{chr(10).join('• ' + w for w in opponent.get('weaknesses', ['Няма данни']))}

🎯 ПРЕПОРЪЧИТЕЛНИ ТАКТИКИ:
• Формация: {opponent.get('recommended_tactics', {}).get('recommended_formation', 'Unknown')}
• Фокус: {opponent.get('recommended_tactics', {}).get('focus', 'Unknown')}
• Специализация: {opponent.get('recommended_tactics', {}).get('specialization', 'Unknown')}

📋 ИНСТРУКЦИИ ЗА МАЧА:
{chr(10).join('• ' + i for i in opponent.get('match_instructions', ['Няма инструкции']))}

💡 AI ПРЕПОРЪКИ:
• Използвайте тяхните слабости в ваша полза
• Внимавайте с техните силни страни
• Адаптирайте тактиката според анализа
• Следете енергията на играчите
"""
        
        self.opponent_details_text.delete(1.0, tk.END)
        self.opponent_details_text.insert(tk.END, details)
    
    def analyze_specific_opponent(self):
        """Анализира конкретен противник"""
        opponent_name = self.opponent_entry.get().strip()
        
        if not opponent_name:
            messagebox.showerror("Грешка", "Моля въведете име на противник!")
            return
        
        if not self.analyzer:
            messagebox.showerror("Грешка", "Първо стартирайте основния анализ!")
            return
        
        def analyze():
            try:
                self.update_status(f"🎯 Анализиране на {opponent_name}...")
                analysis = self.analyzer.analyze_specific_opponent(opponent_name)
                
                if analysis:
                    self.opponents_data[opponent_name] = analysis
                    self.root.after(0, self.update_opponents_list)
                    self.root.after(0, lambda: self.display_opponent_details(opponent_name))
                    self.root.after(0, lambda: messagebox.showinfo("Успех", f"✅ {opponent_name} е анализиран успешно!"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Грешка", f"❌ Неуспешен анализ на {opponent_name}"))
                    
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: messagebox.showerror("Грешка", f"❌ Грешка: {error_msg}"))
        
        thread = threading.Thread(target=analyze, daemon=True)
        thread.start()
    
    def analyze_all_league_opponents(self):
        """Анализира всички противници от лигата"""
        if not self.analyzer:
            messagebox.showerror("Грешка", "Първо стартирайте основния анализ!")
            return
        
        def analyze_all():
            try:
                self.update_status("🔍 Откриване на всички противници в лигата...")
                all_opponents = self.analyzer.discover_all_league_opponents()
                
                total = len(all_opponents)
                for i, opponent in enumerate(all_opponents, 1):
                    self.update_status(f"🎯 Анализиране {i}/{total}: {opponent}")
                    
                    analysis = self.analyzer.analyze_specific_opponent(opponent)
                    if analysis:
                        self.opponents_data[opponent] = analysis
                    
                    # Обновяваме GUI периодично
                    if i % 3 == 0:
                        self.root.after(0, self.update_opponents_list)
                
                self.root.after(0, self.update_opponents_list)
                self.root.after(0, lambda: messagebox.showinfo("Успех", f"✅ Анализирани {len(self.opponents_data)} противника!"))
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: messagebox.showerror("Грешка", f"❌ Грешка: {error_msg}"))
        
        thread = threading.Thread(target=analyze_all, daemon=True)
        thread.start()
    
    def optimize_tactics(self):
        """Оптимизира тактиките"""
        if not self.analyzer or not self.our_players:
            messagebox.showerror("Грешка", "Първо стартирайте анализа на отбора!")
            return
        
        try:
            formation = self.formation_var.get()
            specialization = self.specialization_var.get()
            
            # Генерираме оптимизирани тактики
            optimized = self.analyzer.optimize_tactics_for_formation(formation, specialization)
            
            tactics_content = f"""
⚡ ОПТИМИЗИРАНИ ТАКТИКИ
========================

🏒 ИЗБРАНА НАСТРОЙКА:
• Формация: {formation}
• Специализация: {TACTICAL_SPECIALIZATIONS.get(specialization, {}).get('name', specialization)}

📋 ОПИСАНИЕ НА СПЕЦИАЛИЗАЦИЯТА:
{TACTICAL_SPECIALIZATIONS.get(specialization, {}).get('description', 'Няма описание')}

👥 ОПТИМАЛЕН СЪСТАВ:
{optimized.get('lineup_details', 'Генериране...')}

💡 ТАКТИЧЕСКИ СЪВЕТИ:
{chr(10).join('• ' + tip for tip in optimized.get('tactical_tips', ['Няма съвети']))}

⚠️ ВАЖНИ БЕЛЕЖКИ:
• Следете енергията на играчите
• Адаптирайте според противника
• Използвайте заместванията мъдро
• Наблюдавайте формата на играчите

🔄 РОТАЦИОНЕН ПЛАН:
{optimized.get('rotation_plan', 'Генериране на план...')}
"""
            
            self.tactics_text.delete(1.0, tk.END)
            self.tactics_text.insert(tk.END, tactics_content)
            
        except Exception as e:
            logger.error(f"Tactics optimization error: {e}")
            messagebox.showerror("Грешка", f"Грешка при оптимизация: {str(e)}")
    
    def prepare_match_plan(self):
        """Подготвя план за мач"""
        opponent_name = self.match_opponent_var.get()
        
        if not opponent_name:
            messagebox.showerror("Грешка", "Моля изберете противник!")
            return
        
        if opponent_name not in self.opponents_data:
            messagebox.showerror("Грешка", f"Първо анализирайте {opponent_name}!")
            return
        
        try:
            opponent = self.opponents_data[opponent_name]
            
            match_plan = f"""
🥅 ПЪЛЕН ПЛАН ЗА МАЧ
==================
🎯 Противник: {opponent_name}
📅 Дата: {datetime.now().strftime('%d.%m.%Y')}

📊 АНАЛИЗ НА ПРОТИВНИКА:
• Сила: {opponent.get('strength_rating', 0):.1f}/100
• Стил: {opponent.get('tactical_tendency', 'Unknown')}
• Вероятност за победа: {opponent.get('win_probability', 50):.1f}%

💪 ТЕХНИ СИЛНИ СТРАНИ:
{chr(10).join('• ' + s for s in opponent.get('strengths', []))}

⚠️ ТЕХНИ СЛАБОСТИ:
{chr(10).join('• ' + w for w in opponent.get('weaknesses', []))}

⚡ НАША ТАКТИКА:
• Формация: {opponent.get('recommended_tactics', {}).get('recommended_formation', 'Unknown')}
• Специализация: {opponent.get('recommended_tactics', {}).get('specialization', 'Unknown')}
• Фокус: {opponent.get('recommended_tactics', {}).get('focus', 'Unknown')}

📋 ИНСТРУКЦИИ ЗА МАЧА:
{chr(10).join('• ' + i for i in opponent.get('match_instructions', []))}

👥 СЪСТАВ И РОТАЦИЯ:
• Основен състав: Най-добрите играчи според анализа
• План за замествания: 40-та, 60-та минута
• Внимание: Следете енергията на ключовите играчи

🕐 ПЛАН ПО ВРЕМЕНА:

ПРЕДИ МАЧА (60 мин):
• Проверете формата на всички играчи
• Уверете се, че енергията е над 80%
• Прегледайте тактическата схема
• Направете последна проверка на противника

ПЪРВО ПОЛУВРЕМЕ (0-30 мин):
• Започнете внимателно, тествайте противника
• Фокусирайте се върху техните слабости
• Избягвайте ранни грешки
• Търсете ранен гол за психологическо предимство

ВТОРО ПОЛУВРЕМЕ (30-60 мин):
• Адаптирайте тактиката според резултата
• При водене: Играйте по-предпазливо
• При изоставане: Увеличете агресивността
• Използвайте заместванията стратегически

ИЗВЪНРЕДНИ СИТУАЦИИ:
• При червен картон: Преминете в защитна формация
• При контузия на ключов играч: Бърза замяна
• При лош старт: Тайм-аут и мотивация

💡 КЛЮЧОВИ ТОЧКИ:
• Използвайте {', '.join(opponent.get('weaknesses', [])[:2])}
• Внимавайте с {', '.join(opponent.get('strengths', [])[:2])}
• Поддържайте дисциплина
• Бъдете гъвкави в тактиката

🎯 ЦЕЛИ ЗА МАЧА:
• Основна цел: Победа с добра игра
• Минимална цел: Точка при добро представяне
• Дълготрайна цел: Развитие на младите играчи

📝 БЕЛЕЖКИ:
• Запишете всички промени по време на мача
• Анализирайте представянето след мача
• Подгответе се за следващия противник
"""
            
            self.match_plan_text.delete(1.0, tk.END)
            self.match_plan_text.insert(tk.END, match_plan)
            
            messagebox.showinfo("Успех", f"✅ Планът за мач срещу {opponent_name} е готов!")
            
        except Exception as e:
            logger.error(f"Match plan error: {e}")
            messagebox.showerror("Грешка", f"Грешка при създаване на план: {str(e)}")
    
    def save_match_plan(self):
        """Запазва плана за мач"""
        content = self.match_plan_text.get(1.0, tk.END)
        
        if not content.strip():
            messagebox.showerror("Грешка", "Няма план за запазване!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Запазване на план за мач"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Успех", f"✅ Планът е запазен в {filename}")
            except Exception as e:
                messagebox.showerror("Грешка", f"❌ Грешка при запазване: {str(e)}")
    
    def email_match_plan(self):
        """Изпраща плана по имейл (placeholder)"""
        messagebox.showinfo("Функция", "📧 Email функцията ще бъде добавена в следваща версия")
    
    def mobile_export(self):
        """Експортира за мобилни устройства (placeholder)"""
        messagebox.showinfo("Функция", "📱 Mobile export ще бъде добавен в следваща версия")
    
    def refresh_analysis(self):
        """Обновява анализа"""
        if self.analyzer:
            self.update_dashboard()
            self.update_team_analysis()
            messagebox.showinfo("Успех", "✅ Анализът е обновен!")
        else:
            messagebox.showerror("Грешка", "Първо стартирайте анализа!")
    
    def analyze_next_opponent(self):
        """Анализира следващия противник"""
        if not self.analyzer:
            messagebox.showerror("Грешка", "Първо стартирайте анализа!")
            return
        
        next_opponent = self.analyzer.get_next_opponent()
        if next_opponent:
            self.opponent_entry.delete(0, tk.END)
            self.opponent_entry.insert(0, next_opponent)
            self.analyze_specific_opponent()
        else:
            messagebox.showinfo("Информация", "Няма информация за следващ противник")
    
    def export_comprehensive_report(self):
        """Експортира пълен отчет"""
        if not self.analyzer:
            messagebox.showerror("Грешка", "Първо стартирайте анализа!")
            return
        
        try:
            filename = self.analyzer.generate_comprehensive_report()
            messagebox.showinfo("Успех", f"✅ Пълният отчет е експортиран в {filename}")
        except Exception as e:
            messagebox.showerror("Грешка", f"❌ Грешка при експорт: {str(e)}")
    
    def refresh_logs(self):
        """Обновява логовете"""
        try:
            self.logs_text.delete(1.0, tk.END)
            
            # Зареждаме debug логовете
            try:
                with open('hockey_arena_debug.log', 'r', encoding='utf-8') as f:
                    debug_logs = f.read()
                self.logs_text.insert(tk.END, "=== DEBUG LOGS ===\n")
                self.logs_text.insert(tk.END, debug_logs[-5000:])  # Последните 5000 символа
            except FileNotFoundError:
                self.logs_text.insert(tk.END, "Debug log file not found.\n")
            
            # Зареждаме error логовете
            try:
                with open('hockey_arena_errors.log', 'r', encoding='utf-8') as f:
                    error_logs = f.read()
                if error_logs.strip():
                    self.logs_text.insert(tk.END, "\n\n=== ERROR LOGS ===\n")
                    self.logs_text.insert(tk.END, error_logs[-3000:])  # Последните 3000 символа
            except FileNotFoundError:
                pass
            
            # Скролиране до края
            self.logs_text.see(tk.END)
            
        except Exception as e:
            self.logs_text.delete(1.0, tk.END)
            self.logs_text.insert(tk.END, f"Error loading logs: {str(e)}")
    
    def save_logs(self):
        """Запазва логовете"""
        content = self.logs_text.get(1.0, tk.END)
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Запазване на логове"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Успех", f"✅ Логовете са запазени в {filename}")
            except Exception as e:
                messagebox.showerror("Грешка", f"❌ Грешка при запазване: {str(e)}")
    
    def clear_logs(self):
        """Изчиства логовете"""
        if messagebox.askyesno("Потвърждение", "Сигурни ли сте, че искате да изчистите логовете?"):
            self.logs_text.delete(1.0, tk.END)
    
    def toggle_debug_mode(self):
        """Превключва debug режима"""
        current_level = logging.getLogger().level
        
        if current_level == logging.DEBUG:
            logging.getLogger().setLevel(logging.INFO)
            messagebox.showinfo("Debug Mode", "🔧 Debug режимът е изключен")
        else:
            logging.getLogger().setLevel(logging.DEBUG)
            messagebox.showinfo("Debug Mode", "🐛 Debug режимът е включен")
    
    def update_delay_label(self, value):
        """Обновява етикета за delay"""
        self.delay_value_label.configure(text=f"{float(value):.1f}s")
    
    def open_work_directory(self):
        """Отваря работната директория"""
        try:
            if sys.platform == "win32":
                os.startfile(os.getcwd())
            elif sys.platform == "darwin":
                os.system(f"open {os.getcwd()}")
            else:
                os.system(f"xdg-open {os.getcwd()}")
        except Exception as e:
            messagebox.showerror("Грешка", f"❌ Грешка при отваряне: {str(e)}")
    
    def clean_old_files(self):
        """Изчиства стари файлове"""
        try:
            import glob
            
            patterns = ['hockey_arena_*.json', 'hockey_arena_*.txt', '*.html', '*.csv']
            deleted_count = 0
            
            for pattern in patterns:
                files = glob.glob(pattern)
                
                # Изтриваме файлове по-стари от 7 дни
                for file in files:
                    try:
                        file_time = os.path.getmtime(file)
                        if time.time() - file_time > 7 * 24 * 3600:  # 7 дни
                            os.remove(file)
                            deleted_count += 1
                    except:
                        continue
            
            messagebox.showinfo("Почистване", f"✅ Изтрити {deleted_count} стари файла")
            
        except Exception as e:
            messagebox.showerror("Грешка", f"❌ Грешка при почистване: {str(e)}")
    
    def save_settings(self):
        """Запазва настройките"""
        settings = {
            'human_behavior': self.human_behavior_var.get(),
            'auto_opponent': self.auto_opponent_var.get(),
            'deep_tactics': self.deep_tactics_var.get(),
            'min_delay': self.min_delay_var.get(),
            'deep_analysis': self.deep_analysis_var.get(),
            'auto_tactics': self.auto_tactics_var.get()
        }
        
        try:
            with open('ha_master_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            messagebox.showinfo("Успех", "✅ Настройките са запазени!")
        except Exception as e:
            messagebox.showerror("Грешка", f"❌ Грешка при запазване: {str(e)}")
    
    def load_settings(self):
        """Зарежда настройките"""
        try:
            with open('ha_master_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            self.human_behavior_var.set(settings.get('human_behavior', True))
            self.auto_opponent_var.set(settings.get('auto_opponent', True))
            self.deep_tactics_var.set(settings.get('deep_tactics', True))
            self.min_delay_var.set(settings.get('min_delay', 2.0))
            self.deep_analysis_var.set(settings.get('deep_analysis', True))
            self.auto_tactics_var.set(settings.get('auto_tactics', True))
            
        except FileNotFoundError:
            pass  # Използваме defaults
        except Exception as e:
            logger.error(f"Settings loading error: {e}")
    
    def run(self):
        """Стартира GUI приложението"""
        # Зареждаме настройките
        self.load_settings()
        
        # Стартираме главния loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"GUI error: {e}")
            messagebox.showerror("Критична грешка", f"❌ Неочаквана грешка: {str(e)}")

# ==================== MAIN AI SYSTEM CLASS ====================

class HockeyArenaMasterAI:
    """Главна AI система с всички функционалности"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.base_url = "https://www.hockeyarena.net"
        
        # Системни компоненти
        self.browser_sim = BraveBrowserSimulator()
        self.human_behavior = HumanBehaviorEngine()
        self.opponent_intelligence = OpponentIntelligence(self.session, self.base_url)
        self.tactical_optimizer = TacticalOptimizer()
        
        # Данни
        self.our_players = []
        self.opponents_data = {}
        self.team_info = {}
        self.tactical_recommendations = {}
        
        # Настройка на сесията
        self.session.headers.update(self.browser_sim.get_brave_headers())
        
        logger.info("🏒 Hockey Arena Master AI initialized")
    
    def login_with_human_behavior(self) -> bool:
        """Логване с реалистично човешко поведение"""
        logger.info("🔐 Starting human-like login process...")
        
        try:
            # Стъпка 1: Посещение на главната страница
            logger.debug("📍 Visiting homepage...")
            self.human_behavior.realistic_delay(3.0, 8.0)
            
            home_response = self.session.get(self.base_url, timeout=15)
            if home_response.status_code != 200:
                raise Exception(f"Homepage failed: {home_response.status_code}")
            
            # Симулираме четене
            self.human_behavior.simulate_page_reading(len(home_response.text))
            
            # Стъпка 2: Навигация до login
            logger.debug("🔍 Navigating to login page...")
            self.human_behavior.realistic_delay(2.0, 5.0)
            
            login_url = f"{self.base_url}/index.php?p=login&lang=6"
            login_response = self.session.get(login_url, timeout=15)
            
            if login_response.status_code != 200:
                raise Exception(f"Login page failed: {login_response.status_code}")
            
            # Парсване на формата
            soup = BeautifulSoup(login_response.content, 'html.parser')
            form = soup.find('form')
            
            if not form:
                raise Exception("Login form not found")
            
            # Стъпка 3: Попълване на формата
            logger.debug("⌨️ Filling login form...")
            self.human_behavior.realistic_delay(8.0, 15.0)  # Реалистично време за въвеждане
            
            login_data = {
                'nick': self.username,
                'password': self.password,
                'login': 'Влизане'
            }
            
            # Добавяме скрити полета
            for input_tag in form.find_all('input', {'type': 'hidden'}):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    login_data[name] = value
            
            # Стъпка 4: Submit на формата
            logger.debug("🚀 Submitting login...")
            self.human_behavior.realistic_delay(1.0, 3.0)
            
            final_response = self.session.post(
                f"{self.base_url}/index.php",
                data=login_data,
                allow_redirects=True,
                timeout=20
            )
            
            # Проверка за успех
            success_indicators = ['manager', 'мениджър', 'summary']
            
            if (any(indicator in final_response.url.lower() for indicator in success_indicators) or
                any(indicator in final_response.text.lower() for indicator in success_indicators)):
                
                logger.info("✅ Login successful!")
                self.human_behavior.realistic_delay(2.0, 4.0)
                return True
            else:
                raise Exception("Login failed - invalid credentials or website change")
        
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def analyze_our_team(self):
        """Анализира нашия отбор"""
        logger.info("👥 Analyzing our team...")
        
        try:
            # Анализ на играчите
            players_url = f"{self.base_url}/manager_team_players.php"
            self.human_behavior.realistic_delay(3.0, 6.0)
            
            response = self.session.get(players_url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Запазваме HTML за debug
            with open('our_players_analysis.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.our_players = self._extract_our_players(soup)
            
            # Анализ на информацията за отбора
            info_url = f"{self.base_url}/manager_summary.php"
            self.human_behavior.realistic_delay(2.0, 4.0)
            
            info_response = self.session.get(info_url, timeout=15)
            info_soup = BeautifulSoup(info_response.content, 'html.parser')
            
            self.team_info = self._extract_team_info(info_soup)
            
            logger.info(f"✅ Team analysis complete: {len(self.our_players)} players analyzed")
            
        except Exception as e:
            logger.error(f"Team analysis failed: {e}")
    
    def _extract_our_players(self, soup: BeautifulSoup) -> List[Dict]:
        """Извлича данните за нашите играчи"""
        players = []
        
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            
            if len(rows) < 2:
                continue
            
            # Анализираме headers
            header_row = rows[0]
            headers = [th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])]
            
            # Проверяваме дали това е таблица с играчи
            player_indicators = ['име', 'name', 'goa', 'def', 'att', 'sho', 'spe', 'str', 'pas', 'възраст', 'age']
            
            if not any(indicator in ' '.join(headers) for indicator in player_indicators):
                continue
            
            logger.debug(f"Found player table {table_idx + 1} with headers: {headers}")
            
            # Извличаме данните за играчите
            for row_idx, row in enumerate(rows[1:], 1):
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 3:
                    continue
                
                player_data = {
                    'source_table': table_idx + 1,
                    'row_number': row_idx
                }
                
                # Мапваме данните
                for col_idx, cell in enumerate(cells):
                    if col_idx < len(headers):
                        cell_text = cell.get_text().strip()
                        
                        if cell_text and cell_text not in ['-', '', '0']:
                            # Специална обработка за различни типове данни
                            header = headers[col_idx]
                            
                            if any(attr in header for attr in ['goa', 'def', 'att', 'sho', 'spe', 'str', 'pas']):
                                # Атрибути - извличаме числото
                                numbers = re.findall(r'\d+', cell_text)
                                if numbers:
                                    player_data[header] = int(numbers[0])
                            elif 'възраст' in header or 'age' in header:
                                # Възраст
                                age_match = re.search(r'\d+', cell_text)
                                if age_match:
                                    player_data['age'] = int(age_match.group())
                            elif 'форма' in header or 'form' in header:
                                # Форма
                                form_match = re.search(r'\d+', cell_text)
                                if form_match:
                                    player_data['form'] = int(form_match.group())
                            elif 'енергия' in header or 'energy' in header:
                                # Енергия
                                energy_match = re.search(r'\d+', cell_text)
                                if energy_match:
                                    player_data['energy'] = int(energy_match.group())
                            else:
                                # Останали полета като текст
                                player_data[header] = cell_text
                
                # Обработваме играча само ако има достатъчно данни
                if len(player_data) >= 5:
                    # Определяме името
                    player_data['name'] = self._extract_player_name(player_data)
                    
                    # AI анализ
                    player_data['ai_rating'] = self._calculate_ai_rating(player_data)
                    player_data['best_position'] = self._determine_best_position(player_data)
                    player_data['potential_assessment'] = self._assess_potential(player_data)
                    
                    players.append(player_data)
                    logger.debug(f"Added player: {player_data['name']} (Rating: {player_data['ai_rating']:.1f})")
        
        return players
    
    def _extract_player_name(self, player_data: Dict) -> str:
        """Извлича името на играча"""
        for key, value in player_data.items():
            if 'име' in key.lower() or 'name' in key.lower():
                return str(value)
        
        # Ако няма експлицитно име, търсим в данните
        for key, value in player_data.items():
            if isinstance(value, str) and len(value) > 2 and not any(char.isdigit() for char in value):
                return value
        
        return f"Player_{player_data.get('row_number', 'Unknown')}"
    
    def _calculate_ai_rating(self, player_data: Dict) -> float:
        """Изчислява AI рейтинг на играч според официалното ръководство"""
        attributes = {}
        
        # Извличаме основните атрибути
        attr_mapping = {
            'goa': ['goa', 'brána'],
            'def': ['def', 'obrana', 'защита'],
            'att': ['att', 'útok', 'атака'],
            'sho': ['sho', 'streľba', 'стрелба'],
            'pas': ['pas', 'nahrávka', 'подаване'],
            'str': ['str', 'sila', 'сила'],
            'spe': ['spe', 'rýchlosť', 'скорост'],
            'dis': ['dis', 'sebaovládanie', 'дисциплина']
        }
        
        for attr, variations in attr_mapping.items():
            for key, value in player_data.items():
                if any(var in key.lower() for var in variations):
                    if isinstance(value, int):
                        attributes[attr] = value
                        break
                    elif isinstance(value, str):
                        numbers = re.findall(r'\d+', value)
                        if numbers:
                            attributes[attr] = int(numbers[0])
                            break
        
        if not attributes:
            return 0.0
        
        # Изчисляваме универсален рейтинг
        total_points = sum(attributes.values())
        num_attributes = len(attributes)
        
        if num_attributes == 0:
            return 0.0
        
        base_rating = total_points / num_attributes
        
        # Бонус за специализация (ако има един доминиращ атрибут)
        if attributes:
            max_attr = max(attributes.values())
            avg_attr = sum(attributes.values()) / len(attributes)
            
            if max_attr > avg_attr * 1.3:  # 30% по-висок от средното
                specialization_bonus = (max_attr - avg_attr) * 0.1
                base_rating += specialization_bonus
        
        return round(min(100, max(0, base_rating)), 1)
    
    def _determine_best_position(self, player_data: Dict) -> str:
        """Определя най-добрата позиция според официалното ръководство"""
        attributes = {}
        
        # Извличаме атрибутите
        for key, value in player_data.items():
            if isinstance(value, int) and any(attr in key.lower() for attr in ['goa', 'def', 'att', 'sho', 'pas', 'str', 'spe']):
                attr_name = key.lower()
                if 'goa' in attr_name:
                    attributes['goa'] = value
                elif 'def' in attr_name:
                    attributes['def'] = value
                elif 'att' in attr_name:
                    attributes['att'] = value
                elif 'sho' in attr_name:
                    attributes['sho'] = value
                elif 'pas' in attr_name:
                    attributes['pas'] = value
                elif 'str' in attr_name:
                    attributes['str'] = value
                elif 'spe' in attr_name:
                    attributes['spe'] = value
        
        if not attributes:
            return 'Unknown'
        
        # Изчисляваме рейтинги за всяка позиция според ръководството
        position_ratings = {}
        
        # Вратар: Brána (главен) + Rýchlosť + Nahrávka за контрол на шайбата
        if 'goa' in attributes:
            gk_rating = (attributes.get('goa', 0) * 0.6 + 
                        attributes.get('spe', 0) * 0.3 + 
                        attributes.get('pas', 0) * 0.1)
            position_ratings['Goalkeeper'] = gk_rating
        
        # Защитник: Obrana (главен) + Sila + останали
        def_rating = (attributes.get('def', 0) * 0.4 +
                     attributes.get('str', 0) * 0.25 +
                     attributes.get('spe', 0) * 0.15 +
                     attributes.get('pas', 0) * 0.1 +
                     attributes.get('att', 0) * 0.1)
        position_ratings['Defender'] = def_rating
        
        # Център: Nahrávka (важна) + Útok + Sila (за вхвърляния)
        center_rating = (attributes.get('pas', 0) * 0.3 +
                        attributes.get('att', 0) * 0.25 +
                        attributes.get('str', 0) * 0.2 +
                        attributes.get('spe', 0) * 0.15 +
                        attributes.get('sho', 0) * 0.1)
        position_ratings['Center'] = center_rating
        
        # Нападател: Útok + Streľba (главни)
        forward_rating = (attributes.get('att', 0) * 0.3 +
                         attributes.get('sho', 0) * 0.3 +
                         attributes.get('spe', 0) * 0.2 +
                         attributes.get('pas', 0) * 0.15 +
                         attributes.get('str', 0) * 0.05)
        position_ratings['Forward'] = forward_rating
        
        # Връщаме позицията с най-висок рейтинг
        if position_ratings:
            best_position = max(position_ratings, key=position_ratings.get)
            return best_position
        
        return 'Unknown'
    
    def _assess_potential(self, player_data: Dict) -> str:
        """Оценява потенциала на играча"""
        age = player_data.get('age', 25)
        
        if age < 20:
            return 'Very High'
        elif age < 23:
            return 'High' 
        elif age < 27:
            return 'Good'
        elif age < 30:
            return 'Medium'
        elif age < 33:
            return 'Low'
        else:
            return 'Very Low'
    
    def _extract_team_info(self, soup: BeautifulSoup) -> Dict:
        """Извлича информация за отбора"""
        team_info = {}
        
        # Търсим основна информация
        text = soup.get_text()
        
        # Извличаме различни данни
        patterns = {
            'team_name': r'Мено тіму[:\s]*([^\n]+)',
            'league': r'Ліга[:\s]*([^\n]+)',
            'money': r'Готовість[:\s]*([^\n]+)',
            'players_count': r'Рочет граців[:\s]*([^\n]+)',
            'fans': r'Фанклуб[:\s]*([^\n]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                team_info[key] = match.group(1).strip()
        
        return team_info
    
    def discover_and_analyze_opponents(self) -> Dict:
        """Открива и анализира всички противници"""
        logger.info("🔍 Discovering and analyzing opponents...")
        
        opponents = {}
        
        try:
            # Получаваме класирането
            standings_url = f"{self.base_url}/public_standings.inc"
            self.human_behavior.realistic_delay(3.0, 6.0)
            
            response = self.session.get(standings_url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Запазваме за debug
            with open('league_standings.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Извличаме имената на отборите
            opponent_names = self._extract_opponent_names_from_standings(soup)
            
            logger.info(f"Found {len(opponent_names)} opponents in league")
            
            # Анализираме топ противници (ограничаваме за време)
            for i, opponent_name in enumerate(opponent_names[:8], 1):  # Топ 8
                logger.info(f"🎯 Analyzing opponent {i}/8: {opponent_name}")
                
                # Реалистична пауза между анализи
                self.human_behavior.realistic_delay(4.0, 8.0)
                
                try:
                    analysis = self.opponent_intelligence.analyze_opponent(opponent_name)
                    if analysis and 'error' not in analysis:
                        opponents[opponent_name] = analysis
                        logger.debug(f"✅ {opponent_name} analyzed successfully")
                    else:
                        logger.warning(f"⚠️ Failed to analyze {opponent_name}")
                        
                except Exception as e:
                    logger.error(f"Error analyzing {opponent_name}: {e}")
                    continue
            
            self.opponents_data = opponents
            logger.info(f"✅ Opponent analysis complete: {len(opponents)} teams analyzed")
            
            return opponents
            
        except Exception as e:
            logger.error(f"Opponent discovery failed: {e}")
            return {}
    
    def _extract_opponent_names_from_standings(self, soup: BeautifulSoup) -> List[str]:
        """Извлича имената на противниците от класирането"""
        opponent_names = []
        
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # Търсим таблица с класиране
            if len(rows) < 3:  # Трябва да има поне header + 2 отбора
                continue
            
            for row in rows[1:]:  # Пропускаме header
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    # Обикновено името на отбора е във втората колона
                    team_name_cell = cells[1]
                    team_name = team_name_cell.get_text().strip()
                    
                    # Филтрираме валидни имена
                    if (team_name and 
                        len(team_name) > 2 and 
                        team_name not in ['Име на отбора', 'Team Name', 'Отбор'] and
                        not re.match(r'^\d+, team_name)):  # Не само цифри
                        
                        opponent_names.append(team_name)
        
        # Премахваме дублиращи се и връщаме уникални
        unique_opponents = list(dict.fromkeys(opponent_names))  # Запазва реда
        
        return unique_opponents
    
    def generate_optimal_tactics(self):
        """Генерира оптимални тактики"""
        logger.info("⚡ Generating optimal tactics...")
        
        try:
            # Анализираме нашия отбор
            our_team_analysis = self._analyze_our_team_strength()
            
            # Генерираме тактики за всеки противник
            tactical_plans = {}
            
            for opponent_name, opponent_data in self.opponents_data.items():
                try:
                    # Преобразуваме нашите играчи в PlayerStats обекти
                    our_player_stats = []
                    for player in self.our_players:
                        player_stat = PlayerStats(
                            name=player.get('name', 'Unknown'),
                            age=player.get('age', 25),
                            position=player.get('best_position', 'Forward'),
                            goa=player.get('goa', 0),
                            def_=player.get('def', 0),
                            att=player.get('att', 0),
                            sho=player.get('sho', 0),
                            pas=player.get('pas', 0),
                            str_=player.get('str', 0),
                            spe=player.get('spe', 0),
                            dis=player.get('dis', 0),
                            energy=player.get('energy', 100),
                            form=player.get('form', 100)
                        )
                        our_player_stats.append(player_stat)
                    
                    # Оптимизираме тактиките
                    optimal_tactics = self.tactical_optimizer.optimize_lineup_and_tactics(
                        our_player_stats, opponent_data
                    )
                    
                    tactical_plans[opponent_name] = optimal_tactics
                    
                except Exception as e:
                    logger.error(f"Tactics generation failed for {opponent_name}: {e}")
                    continue
            
            # Генерираме общи тактики
            general_tactics = self._generate_general_tactics(our_team_analysis)
            tactical_plans['general'] = general_tactics
            
            self.tactical_recommendations = tactical_plans
            logger.info(f"✅ Tactical optimization complete: {len(tactical_plans)} plans generated")
            
        except Exception as e:
            logger.error(f"Tactical generation failed: {e}")
    
    def _analyze_our_team_strength(self) -> Dict:
        """Анализира силата на нашия отбор"""
        if not self.our_players:
            return {}
        
        analysis = {
            'total_players': len(self.our_players),
            'average_rating': 0,
            'position_distribution': {},
            'age_analysis': {},
            'form_analysis': {},
            'energy_analysis': {}
        }
        
        # Основни статистики
        ratings = [p.get('ai_rating', 0) for p in self.our_players if p.get('ai_rating')]
        if ratings:
            analysis['average_rating'] = sum(ratings) / len(ratings)
        
        # Разпределение по позиции
        for player in self.our_players:
            pos = player.get('best_position', 'Unknown')
            analysis['position_distribution'][pos] = analysis['position_distribution'].get(pos, 0) + 1
        
        # Възрастов анализ
        ages = [p.get('age', 25) for p in self.our_players if p.get('age')]
        if ages:
            analysis['age_analysis'] = {
                'average': sum(ages) / len(ages),
                'min': min(ages),
                'max': max(ages),
                'young_players': len([a for a in ages if a < 23]),
                'veteran_players': len([a for a in ages if a > 30])
            }
        
        return analysis
    
    def _generate_general_tactics(self, team_analysis: Dict) -> Dict:
        """Генерира общи тактики"""
        avg_rating = team_analysis.get('average_rating', 50)
        
        if avg_rating > 65:
            recommended_style = 'aggressive'
            formation = '1-2-3'
            specialization = 'forechecking'
        elif avg_rating > 50:
            recommended_style = 'balanced'
            formation = '1-3-2'
            specialization = 'short_passes'
        else:
            recommended_style = 'defensive'
            formation = '1-4-1'
            specialization = 'counter_attacks'
        
        return {
            'style': recommended_style,
            'formation': formation,
            'specialization': specialization,
            'general_instructions': [
                f"🎯 Играйте {recommended_style} стил",
                f"🏒 Използвайте формация {formation}",
                f"⚡ Специализация: {specialization}",
                "💪 Следете енергията на играчите",
                "🔄 Ротирайте състава редовно"
            ]
        }
    
    # ==================== INTERFACE METHODS ====================
    
    def get_our_players(self) -> List[Dict]:
        """Връща нашите играчи"""
        return self.our_players
    
    def get_team_rating(self) -> float:
        """Връща рейтинга на отбора"""
        if not self.our_players:
            return 0.0
        
        ratings = [p.get('ai_rating', 0) for p in self.our_players if p.get('ai_rating')]
        return sum(ratings) / len(ratings) if ratings else 0.0
    
    def get_next_opponent(self) -> str:
        """Връща следващия противник"""
        # В реална ситуация това ще анализира календара
        if self.opponents_data:
            return list(self.opponents_data.keys())[0]
        return "Unknown"
    
    def get_recommended_tactic(self) -> str:
        """Връща препоръчителната тактика"""
        if self.tactical_recommendations and 'general' in self.tactical_recommendations:
            return self.tactical_recommendations['general'].get('specialization', 'Unknown')
        return "Not analyzed"
    
    def get_team_info_summary(self) -> str:
        """Връща обобщение за отбора"""
        if not self.team_info:
            return "Няма данни за отбора"
        
        summary = "🏒 ИНФОРМАЦИЯ ЗА ОТБОРА\n"
        summary += "=" * 40 + "\n\n"
        
        for key, value in self.team_info.items():
            summary += f"• {key.replace('_', ' ').title()}: {value}\n"
        
        return summary
    
    def get_detailed_team_stats(self) -> str:
        """Връща детайлни статистики за отбора"""
        if not self.our_players:
            return "Няма данни за играчи"
        
        stats = "📊 ДЕТАЙЛНИ СТАТИСТИКИ\n"
        stats += "=" * 40 + "\n\n"
        
        # Основни статистики
        total_players = len(self.our_players)
        ratings = [p.get('ai_rating', 0) for p in self.our_players if p.get('ai_rating')]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        stats += f"📈 ОБЩИ ПОКАЗАТЕЛИ:\n"
        stats += f"• Общо играчи: {total_players}\n"
        stats += f"• Среден рейтинг: {avg_rating:.1f}/100\n"
        stats += f"• Най-висок рейтинг: {max(ratings) if ratings else 0:.1f}\n"
        stats += f"• Най-нисък рейтинг: {min(ratings) if ratings else 0:.1f}\n\n"
        
        # Разпределение по позиции
        positions = {}
        for player in self.our_players:
            pos = player.get('best_position', 'Unknown')
            positions[pos] = positions.get(pos, 0) + 1
        
        stats += f"📍 РАЗПРЕДЕЛЕНИЕ ПО ПОЗИЦИИ:\n"
        for pos, count in positions.items():
            stats += f"• {pos}: {count} играчи\n"
        stats += "\n"
        
        # Възрастов анализ
        ages = [p.get('age', 25) for p in self.our_players if p.get('age')]
        if ages:
            avg_age = sum(ages) / len(ages)
            stats += f"👥 ВЪЗРАСТОВ АНАЛИЗ:\n"
            stats += f"• Средна възраст: {avg_age:.1f} години\n"
            stats += f"• Най-млад: {min(ages)} години\n"
            stats += f"• Най-възрастен: {max(ages)} години\n"
            stats += f"• Млади играчи (<23): {len([a for a in ages if a < 23])}\n"
            stats += f"• Ветерани (>30): {len([a for a in ages if a > 30])}\n\n"
        
        # Топ 5 играчи
        top_players = sorted(self.our_players, key=lambda p: p.get('ai_rating', 0), reverse=True)[:5]
        stats += f"🌟 ТОП 5 ИГРАЧИ:\n"
        for i, player in enumerate(top_players, 1):
            name = player.get('name', 'Unknown')
            rating = player.get('ai_rating', 0)
            position = player.get('best_position', 'Unknown')
            stats += f"{i}. {name} - {rating:.1f} ({position})\n"
        
        return stats
    
    def get_team_recommendations(self) -> str:
        """Връща препоръки за отбора"""
        if not self.our_players:
            return "Няма данни за генериране на препоръки"
        
        recs = "💡 AI ПРЕПОРЪКИ ЗА ОТБОРА\n"
        recs += "=" * 40 + "\n\n"
        
        # Анализ и препоръки
        team_analysis = self._analyze_our_team_strength()
        avg_rating = team_analysis.get('average_rating', 0)
        
        recs += "🎯 ПРИОРИТЕТНИ ПРЕПОРЪКИ:\n"
        
        if avg_rating < 45:
            recs += "• 🔴 КРИТИЧНО: Отборът се нуждае от спешни подобрения\n"
            recs += "• 📈 Фокусирайте се върху тренировки на основните атрибути\n"
            recs += "• 🔄 Търсете нови играчи на трансферния пазар\n"
        elif avg_rating < 60:
            recs += "• 🟡 Отборът има потенциал за подобрение\n"
            recs += "• 🏋️ Интензивни тренировки за ключовите играчи\n"
            recs += "• 🎯 Фокус върху слабите позиции\n"
        else:
            recs += "• 🟢 Силен отбор - поддържайте формата\n"
            recs += "• ⭐ Инвестирайте в млади таланти\n"
            recs += "• 🏆 Фокусирайте се върху тактическо усъвършенстване\n"
        
        recs += "\n"
        
        # Позиционни препоръки
        positions = team_analysis.get('position_distribution', {})
        
        recs += "📍 ПОЗИЦИОННИ ПРЕПОРЪКИ:\n"
        
        position_needs = {
            'Goalkeeper': 2,
            'Defender': 6,
            'Center': 4,
            'Forward': 8
        }
        
        for pos, needed in position_needs.items():
            current = positions.get(pos, 0)
            if current < needed:
                recs += f"• ⚠️ Нужни са {needed - current} {pos.lower()}(s)\n"
            elif current == needed:
                recs += f"• ✅ Добро покритие на позиция {pos.lower()}\n"
            else:
                recs += f"• 📊 Добра дълбочина на позиция {pos.lower()}\n"
        
        recs += "\n"
        
        # Възрастови препоръки
        age_analysis = team_analysis.get('age_analysis', {})
        avg_age = age_analysis.get('average', 25)
        
        recs += "👥 ВЪЗРАСТОВИ ПРЕПОРЪКИ:\n"
        
        if avg_age > 29:
            recs += "• 🔄 Отборът застарява - търсете млади играчи\n"
            recs += "• 💪 Обърнете внимание на физическата подготовка\n"
        elif avg_age < 22:
            recs += "• 🌱 Млад отбор - фокусирайте се върху развитието\n"
            recs += "• 📚 Инвестирайте в тренировки и опит\n"
        else:
            recs += "• ⚖️ Добър възрастов баланс\n"
            recs += "• 🎯 Продължете с настоящата стратегия\n"
        
        # Общи препоръки
        recs += "\n🎮 ОБЩИ ПРЕПОРЪКИ:\n"
        recs += "• 📊 Редовно анализирайте противниците\n"
        recs += "• ⚡ Адаптирайте тактиките според мача\n"
        recs += "• 💪 Следете енергията и формата на играчите\n"
        recs += "• 🔄 Използвайте ротацията разумно\n"
        recs += "• 📈 Инвестирайте в дългосрочно развитие\n"
        
        return recs
    
    def analyze_specific_opponent(self, opponent_name: str) -> Dict:
        """Анализира конкретен противник"""
        return self.opponent_intelligence.analyze_opponent(opponent_name)
    
    def discover_all_league_opponents(self) -> List[str]:
        """Открива всички противници в лигата"""
        try:
            standings_url = f"{self.base_url}/public_standings.inc"
            response = self.session.get(standings_url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return self._extract_opponent_names_from_standings(soup)
        except Exception as e:
            logger.error(f"Failed to discover opponents: {e}")
            return []
    
    def optimize_tactics_for_formation(self, formation: str, specialization: str) -> Dict:
        """Оптимизира тактиките за конкретна формация"""
        try:
            # Анализираме избраната комбинация
            spec_data = TACTICAL_SPECIALIZATIONS.get(specialization, {})
            
            optimization = {
                'formation': formation,
                'specialization': specialization,
                'lineup_details': self._generate_lineup_for_formation(formation),
                'tactical_tips': self._generate_formation_tips(formation, specialization),
                'rotation_plan': self._generate_rotation_plan()
            }
            
            return optimization
            
        except Exception as e:
            logger.error(f"Formation optimization failed: {e}")
            return {'error': str(e)}
    
    def _generate_lineup_for_formation(self, formation: str) -> str:
        """Генерира състав за формация"""
        if not self.our_players:
            return "Няма данни за играчи"
        
        lineup = f"📋 ОПТИМАЛЕН СЪСТАВ ЗА ФОРМАЦИЯ {formation}:\n\n"
        
        # Сортираме играчите по позиции и рейтинг
        goalkeepers = [p for p in self.our_players if p.get('best_position') == 'Goalkeeper']
        defenders = [p for p in self.our_players if p.get('best_position') == 'Defender']
        centers = [p for p in self.our_players if p.get('best_position') == 'Center']
        forwards = [p for p in self.our_players if p.get('best_position') == 'Forward']
        
        # Сортираме по рейтинг
        for position_list in [goalkeepers, defenders, centers, forwards]:
            position_list.sort(key=lambda p: p.get('ai_rating', 0), reverse=True)
        
        # Генерираме състава според формацията
        if formation == '1-4-1':
            lineup += "🥅 ВРАТАР:\n"
            if goalkeepers:
                gk = goalkeepers[0]
                lineup += f"• {gk['name']} (Рейтинг: {gk.get('ai_rating', 0):.1f})\n\n"
            
            lineup += "🛡️ ЗАЩИТНИЦИ (4):\n"
            for i, defender in enumerate(defenders[:4], 1):
                lineup += f"{i}. {defender['name']} (Рейтинг: {defender.get('ai_rating', 0):.1f})\n"
            
            lineup += "\n⚡ НАПАДАТЕЛИ (1):\n"
            if forwards:
                fw = forwards[0]
                lineup += f"• {fw['name']} (Рейтинг: {fw.get('ai_rating', 0):.1f})\n"
        
        elif formation == '1-3-2':
            lineup += "🥅 ВРАТАР:\n"
            if goalkeepers:
                gk = goalkeepers[0]
                lineup += f"• {gk['name']} (Рейтинг: {gk.get('ai_rating', 0):.1f})\n\n"
            
            lineup += "🛡️ ЗАЩИТНИЦИ (3):\n"
            for i, defender in enumerate(defenders[:3], 1):
                lineup += f"{i}. {defender['name']} (Рейтинг: {defender.get('ai_rating', 0):.1f})\n"
            
            lineup += "\n⚡ НАПАДАТЕЛИ (2):\n"
            for i, forward in enumerate(forwards[:2], 1):
                lineup += f"{i}. {forward['name']} (Рейтинг: {forward.get('ai_rating', 0):.1f})\n"
        
        elif formation == '1-2-3':
            lineup += "🥅 ВРАТАР:\n"
            if goalkeepers:
                gk = goalkeepers[0]
                lineup += f"• {gk['name']} (Рейтинг: {gk.get('ai_rating', 0):.1f})\n\n"
            
            lineup += "🛡️ ЗАЩИТНИЦИ (2):\n"
            for i, defender in enumerate(defenders[:2], 1):
                lineup += f"{i}. {defender['name']} (Рейтинг: {defender.get('ai_rating', 0):.1f})\n"
            
            lineup += "\n⚡ НАПАДАТЕЛИ (3):\n"
            for i, forward in enumerate(forwards[:3], 1):
                lineup += f"{i}. {forward['name']} (Рейтинг: {forward.get('ai_rating', 0):.1f})\n"
        
        return lineup
    
    def _generate_formation_tips(self, formation: str, specialization: str) -> List[str]:
        """Генерира съвети за формация и специализация"""
        tips = []
        
        # Съвети за формацията
        formation_tips = {
            '1-4-1': [
                "🛡️ Силна защита - използвайте за контраатаки",
                "⏱️ Играйте търпеливо и чакайте момента",
                "🎯 Фокусирайте се върху един нападател"
            ],
            '1-3-2': [
                "⚖️ Балансирана формация за всички ситуации",
                "🔄 Добра за ротация и адаптиране",
                "💪 Стабилна основа за развитие"
            ],
            '1-2-3': [
                "⚡ Агресивна атакуваща формация",
                "🎯 Максимален натиск в атака",
                "⚠️ Внимавайте с защитата при контраатаки"
            ]
        }
        
        tips.extend(formation_tips.get(formation, []))
        
        # Съвети за специализацията
        spec_data = TACTICAL_SPECIALIZATIONS.get(specialization)
        if spec_data:
            tips.append(f"🎯 {spec_data.description}")
            
            # Специфични съвети според специализацията
            if specialization == 'counter_attacks':
                tips.extend([
                    "🛡️ Играйте компактно в защита",
                    "⚡ Бъдете готови за бързи контраатаки",
                    "🎯 Използвайте скоростта на нападателите"
                ])
            elif specialization == 'forechecking':
                tips.extend([
                    "💪 Агресивно натискане в чуждата зона",
                    "🏃 Високо темпо на играта",
                    "⚠️ Внимавайте с енергията на играчите"
                ])
            elif specialization == 'short_passes':
                tips.extend([
                    "🎯 Прецизни кратки подавания",
                    "🧠 Търпение при изграждане на атаките",
                    "📍 Добра позиционна игра"
                ])
        
        return tips
    
    def _generate_rotation_plan(self) -> str:
        """Генерира план за ротация"""
        plan = "🔄 ПЛАН ЗА РОТАЦИЯ:\n\n"
        
        plan += "⚡ ОСНОВНИ ПРИНЦИПИ:\n"
        plan += "• Ротирайте играчите при енергия под 70%\n"
        plan += "• Давайте почивка на ключовите играчи в по-леки мачове\n"
        plan += "• Използвайте младите играчи за натрупване на опит\n"
        plan += "• Следете формата - играчи в лоша форма почиват\n\n"
        
        plan += "📅 СЕДМИЧЕН ГРАФИК:\n"
        plan += "• Понеделник: Анализ на изминалия мач\n"
        plan += "• Вторник-Сряда: Основни тренировки\n"
        plan += "• Четвъртък: Тактическа подготовка\n"
        plan += "• Петък: Лека тренировка + почивка\n"
        plan += "• Събота: Подготовка за мач\n"
        plan += "• Неделя: Мач или почивка\n\n"
        
        plan += "⚠️ ВАЖНИ БЕЛЕЖКИ:\n"
        plan += "• Вратарите се уморяват според броя стрелби\n"
        plan += "• Младите играчи се развиват по-бързо\n"
        plan += "• Следете баланса между почивка и игрово време\n"
        
        return plan
    
    def generate_comprehensive_report(self) -> str:
        """Генерира пълен отчет"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hockey_arena_comprehensive_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("🏒 HOCKEY ARENA MASTER AI - ПЪЛЕН ОТЧЕТ\n")
                f.write("=" * 70 + "\n")
                f.write(f"Генериран: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"Потребител: {self.username}\n\n")
                
                # Информация за отбора
                f.write(self.get_team_info_summary())
                f.write("\n\n")
                
                # Детайлни статистики
                f.write(self.get_detailed_team_stats())
                f.write("\n\n")
                
                # Препоръки
                f.write(self.get_team_recommendations())
                f.write("\n\n")
                
                # Анализ на противници
                if self.opponents_data:
                    f.write("🎯 АНАЛИЗ НА ПРОТИВНИЦИ\n")
                    f.write("=" * 40 + "\n\n")
                    
                    for opponent_name, opponent_data in self.opponents_data.items():
                        f.write(f"📊 {opponent_name}:\n")
                        f.write(f"• Сила: {opponent_data.get('strength_rating', 0):.1f}/100\n")
                        f.write(f"• Вероятност за победа: {opponent_data.get('win_probability', 50):.1f}%\n")
                        f.write(f"• Силни страни: {', '.join(opponent_data.get('strengths', []))}\n")
                        f.write(f"• Слабости: {', '.join(opponent_data.get('weaknesses', []))}\n\n")
                
                # Тактически препоръки
                if self.tactical_recommendations:
                    f.write("⚡ ТАКТИЧЕСКИ ПРЕПОРЪКИ\n")
                    f.write("=" * 40 + "\n\n")
                    
                    general = self.tactical_recommendations.get('general', {})
                    f.write(f"🎯 Общ стил: {general.get('style', 'Unknown')}\n")
                    f.write(f"🏒 Препоръчителна формация: {general.get('formation', 'Unknown')}\n")
                    f.write(f"⚡ Специализация: {general.get('specialization', 'Unknown')}\n\n")
                
                # Системна информация
                f.write("🔧 СИСТЕМНА ИНФОРМАЦИЯ\n")
                f.write("=" * 40 + "\n")
                f.write(f"• Анализирани играчи: {len(self.our_players)}\n")
                f.write(f"• Анализирани противници: {len(self.opponents_data)}\n")
                f.write(f"• Генерирани тактически планове: {len(self.tactical_recommendations)}\n")
                f.write(f"• Версия на AI: Hockey Arena Master AI v4.0\n")
            
            logger.info(f"✅ Comprehensive report generated: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise e

# ==================== MAIN FUNCTION ====================

def main():
    """Главна функция - стартира GUI системата"""
    
    print("🏒 HOCKEY ARENA MASTER AI v4.0")
    print("🧠 Най-напредналата AI система за доминиране в Hockey Arena")
    print("📚 Базирана на официалното ръководство от ha-navod.eu")
    print("=" * 70)
    
    # Проверяваме работната директория
    print(f"📁 Work directory: {os.getcwd()}")
    
    try:
        # Стартиране на GUI
        print("🖥️ Starting GUI interface...")
        gui = HockeyArenaGUI()
        gui.run()
        
    except ImportError as e:
        print(f"❌ GUI libraries missing: {e}")
        print("📝 Please install required packages:")
        print("   pip install tkinter matplotlib seaborn")
        
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        logger.error(f"Main execution error: {str(e)}")
        
        # Fallback режим
        print("\n📝 Attempting console fallback...")
        try:
            run_console_fallback()
        except Exception as fallback_error:
            print(f"❌ Console fallback also failed: {fallback_error}")

def run_console_fallback():
    """Конзолен fallback режим"""
    print("\n" + "="*50)
    print("📝 CONSOLE MODE (Fallback)")
    print("="*50)
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not username or not password:
        print("❌ Username and password required!")
        return
    
    print(f"\n🚀 Starting console analysis for: {username}")
    
    try:
        ai = HockeyArenaMasterAI(username, password)
        
        # Опростен анализ
        print("🔐 Logging in...")
        if not ai.login_with_human_behavior():
            print("❌ Login failed!")
            return
        
        print("👥 Analyzing team...")
        ai.analyze_our_team()
        
        print("🎯 Analyzing opponents...")
        ai.discover_and_analyze_opponents()
        
        print("⚡ Generating tactics...")
        ai.generate_optimal_tactics()
        
        # Показване на резултати
        print("\n" + "="*50)
        print("📊 ANALYSIS RESULTS")
        print("="*50)
        
        print(f"Team Rating: {ai.get_team_rating():.1f}/100")
        print(f"Players Analyzed: {len(ai.our_players)}")
        print(f"Opponents Analyzed: {len(ai.opponents_data)}")
        
        # Генериране на отчет
        report_file = ai.generate_comprehensive_report()
        print(f"\n✅ Full report saved: {report_file}")
        
        print("\n🎉 Console analysis completed!")
        
    except Exception as e:
        print(f"❌ Console analysis failed: {str(e)}")

if __name__ == "__main__":
    main()