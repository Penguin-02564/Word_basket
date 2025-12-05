import random
import json
import os
import uuid
from typing import List, Optional, Set, Dict

class Card:
    def __init__(self, type: str, value: str, display: str):
        self.type = type  # "char", "row", "length"
        self.value = value
        self.display = display

    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "display": self.display
        }

class Player:
    def __init__(self, player_id: str, name: str, is_host: bool = False):
        self.player_id = player_id
        self.name = name
        self.hand: List[Card] = []
        self.is_host = is_host
        self.card_priority: List[str] = ['char', 'row', 'length']
        self.rank: Optional[int] = None

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "name": self.name,
            "hand_count": len(self.hand),
            "is_host": self.is_host,
            "rank": self.rank
        }

class WordBasketGame:
    def __init__(self, room_code: str, dictionary_path: str = None):
        self.room_code = room_code
        self.deck: List[Card] = []
        self.players: Dict[str, Player] = {}
        self.current_word: str = ""
        self.dictionary: Set[str] = set()
        self.status: str = "waiting" # waiting, playing, finished
        self.finished_players: List[Player] = []

        
        if dictionary_path is None:
            dictionary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "words.json")
            
        self.load_dictionary(dictionary_path)
        self.initialize_deck()

    def load_dictionary(self, path: str):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    words = json.load(f)
                    if isinstance(words, list):
                        if words and isinstance(words[0], dict):
                             self.dictionary = {w.get('kana', w.get('reading', '')) for w in words}
                        else:
                            self.dictionary = set(words)
            except Exception as e:
                print(f"Error loading dictionary: {e}")
                self.use_dummy_dictionary()
        else:
            self.use_dummy_dictionary()

    def use_dummy_dictionary(self):
        # Fallback dictionary
        self.dictionary = {
            "りんご", "ゴリラ", "ラッパ", "パンツ", "積み木", "キツネ", "ネコ", "コマ", "マント",
            "トマト", "トランプ", "プリン", "リボン", "スイカ", "カラス", "スズメ", "メダカ",
            "カメラ", "ラクダ", "ダチョウ", "ウシ", "シマウマ", "マクラ", "ラッコ", "コアラ",
            "ライオン", "ンゴロンゴロ", "ロバ", "バイク", "クルマ", "マイク", "クスリ", "リス",
            "スイミング", "グミ", "ミカン", "ンジャメナ", "ナシ", "シカ", "カバ", "バナナ",
            "ナマケモノ", "ノリ", "リクガメ", "メロン", "ン", "ルビー", "ビール", "ルビー",
            "イヌ", "ヌマ", "マリモ", "モチ", "チクワ", "ワニ", "ニワトリ", "トリ", "リスマーク",
            "クライミング", "グライダー", "ダンプカー", "カーテン", "テント", "トンネル", "ルンバ",
            "バスケット", "トースト", "トマトソース", "ステーキ", "キリン", "リンゴジュース",
            "スイス", "スタンプ", "プラモデル", "ルビー", "ビーズ", "ズボン", "ン",
            "アイロン", "ロケット", "トケイ", "イカ", "カニ", "ニジ", "ジドウシャ", "ヤカン",
            "ン", "ルビー", "ビール", "ルビー", "イヌ", "ヌマ", "マリモ", "モチ", "チクワ",
            "ワニ", "ニワトリ", "トリ", "リスマーク", "クライミング", "グライダー", "ダンプカー",
            "カーテン", "テント", "トンネル", "ルンバ", "バスケット", "トースト", "トマトソース",
            "ステーキ", "キリン", "リンゴジュース", "スイス", "スタンプ", "プラモデル", "ルビー",
            "ビーズ", "ズボン", "ン", "アイロン", "ロケット", "トケイ", "イカ", "カニ", "ニジ",
            "ジドウシャ", "ヤカン"
        }

    def initialize_deck(self):
        self.deck = []
        # Hiragana cards
        hiragana = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわを"
        for char in hiragana:
            self.deck.append(Card("char", char, char))
        
        # Row cards
        rows = [
            ("あ行", "あいうえお"), ("か行", "かきくけこ"), ("さ行", "さしすせそ"),
            ("た行", "たちつてと"), ("な行", "なにぬねの"), ("は行", "はひふへほ"),
            ("ま行", "まみむめも"), ("や行", "やゆよ"), ("ら行", "らりるれろ"),
            ("わ行", "わを")
        ]
        for name, chars in rows:
            self.deck.append(Card("row", chars, name))

        # Length cards
        lengths = [5, 6, 7]
        for l in lengths:
            display = f"{l}文字" if l < 7 else "7文字以上"
            val = str(l)
            for _ in range(3):
                self.deck.append(Card("length", val, display))

    def add_player(self, player_id: str, name: str) -> Player:
        is_host = len(self.players) == 0
        player = Player(player_id, name, is_host)
        self.players[player_id] = player
        return player

    def remove_player(self, player_id: str):
        if player_id in self.players:
            del self.players[player_id]
            # If host left, assign new host
            if self.players:
                first_player_id = next(iter(self.players))
                self.players[first_player_id].is_host = True

    def start_game(self):
        self.initialize_deck()
        random.shuffle(self.deck)
        
        # Distribute cards
        for player in self.players.values():
            player.hand = [self.deck.pop() for _ in range(7)]
        
        start_char = random.choice("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろ")
        self.current_word = "ゲーム開始_" + start_char
        self.status = "playing"
        self.finished_players = []
        for p in self.players.values():
            p.rank = None


    def normalize_kana(self, char: str) -> str:
        # 1. Katakana to Hiragana
        if 'ァ' <= char <= 'ン':
            char = chr(ord(char) - 0x60)
        elif char == 'ヵ': char = 'か'
        elif char == 'ヶ': char = 'け'
        elif char == 'ヴ': char = 'う'

        # 2. Remove Dakuten/Handakuten and normalize small ya/yu/yo
        mapping = {
            'が': 'か', 'ぎ': 'き', 'ぐ': 'く', 'げ': 'け', 'ご': 'こ',
            'ざ': 'さ', 'じ': 'し', 'ず': 'す', 'ぜ': 'せ', 'ぞ': 'そ',
            'だ': 'た', 'ぢ': 'ち', 'づ': 'つ', 'で': 'て', 'ど': 'と',
            'ば': 'は', 'び': 'ひ', 'ぶ': 'ふ', 'べ': 'へ', 'ぼ': 'ほ',
            'ぱ': 'は', 'ぴ': 'ひ', 'ぷ': 'ふ', 'ぺ': 'へ', 'ぽ': 'ほ',
            'ゃ': 'や', 'ゅ': 'ゆ', 'ょ': 'よ',
        }
        return mapping.get(char, char)

    def get_target_char(self):
        if not self.current_word:
            return ""
        
        last_char = self.current_word[-1]
        if last_char == "ー" and len(self.current_word) > 1:
            last_char = self.current_word[-2]
        
        return last_char

    def check_move(self, player_id: str, word: str, card_index: int) -> dict:
        if self.status != "playing":
            return {"valid": False, "message": "ゲームは開始されていません"}

        player = self.players.get(player_id)
        if not player:
             return {"valid": False, "message": "プレイヤーが見つかりません"}

        if not (0 <= card_index < len(player.hand)):
            return {"valid": False, "message": "Invalid card index"}
        
        card = player.hand[card_index]
        word = word.strip()

        if word.endswith("ーー"):
             return {"valid": False, "message": "伸ばし棒は連続して使えません"}

        target_char = self.get_target_char()
        
        if not word:
             return {"valid": False, "message": "単語を入力してください"}

        start_char = word[0]
        if self.normalize_kana(start_char) != self.normalize_kana(target_char):
             return {"valid": False, "message": f"「{target_char}」から始まる単語ではありません"}
            
        if word.endswith("ん"):
            return {"valid": False, "message": "「ん」で終わる単語は使えません"}

        min_length = 4 if len(player.hand) == 1 else 3
        if len(word) < min_length:
            return {"valid": False, "message": f"{min_length}文字以上の単語にしてください"}

        valid_card = False
        effective_end = word[-1]
        if word.endswith("ー") and len(word) > 1:
            effective_end = word[-2]
        
        if card.type == "char":
            if self.normalize_kana(effective_end) == self.normalize_kana(card.value):
                valid_card = True
            else:
                return {"valid": False, "message": f"最後が「{card.value}」で終わる単語ではありません"}
        
        elif card.type == "row":
            if self.normalize_kana(effective_end) in card.value:
                valid_card = True
            else:
                return {"valid": False, "message": f"最後が{card.display}で終わる単語ではありません"}
        
        elif card.type == "length":
            req_len = int(card.value)
            if req_len == 7:
                if len(word) >= 7:
                    valid_card = True
                else:
                    return {"valid": False, "message": "7文字以上の単語ではありません"}
            else:
                if len(word) == req_len:
                    valid_card = True
                else:
                    return {"valid": False, "message": f"{req_len}文字の単語ではありません"}


        if valid_card:
            player.hand.pop(card_index)
            self.current_word = word
            
            message = "OK"
            game_over = False
            winner = None

            if len(player.hand) == 0:
                # Player finished
                if player.rank is None:
                    player.rank = len(self.finished_players) + 1
                    self.finished_players.append(player)
                    message = f"{player.name}さんが{player.rank}位で上がりました！"
                
                # Check if game should end
                # Game ends if all players finished OR only 1 player left (if started with > 1)
                active_players_count = len([p for p in self.players.values() if p.rank is None])
                
                if active_players_count == 0:
                    self.status = "finished"
                    game_over = True
                elif active_players_count == 1 and len(self.players) > 1:
                    # Last player gets the last rank
                    last_player = next(p for p in self.players.values() if p.rank is None)
                    last_player.rank = len(self.finished_players) + 1
                    self.finished_players.append(last_player)
                    self.status = "finished"
                    game_over = True
            
            return {
                "valid": True, 
                "message": message, 
                "game_over": game_over, 
                "winner": self.finished_players[0].name if self.finished_players else None,
                "ranks": [p.to_dict() for p in self.finished_players] if game_over else []
            }
        
        return {"valid": False, "message": "不明なエラー"}

    def auto_select_card(self, player_id: str, word: str) -> Optional[int]:
        player = self.players.get(player_id)
        if not player:
            return None

        word = word.strip()
        if not word:
            return None
        
        effective_end = word[-1]
        if word.endswith("ー") and len(word) > 1:
            effective_end = word[-2]
        
        card_indices_by_type = {'char': [], 'row': [], 'length': []}
        
        for idx, card in enumerate(player.hand):
            if card.type == 'char':
                if self.normalize_kana(effective_end) == self.normalize_kana(card.value):
                    card_indices_by_type['char'].append(idx)
            elif card.type == 'row':
                if self.normalize_kana(effective_end) in card.value:
                    card_indices_by_type['row'].append(idx)
            elif card.type == 'length':
                req_len = int(card.value)
                if req_len == 7:
                    if len(word) >= 7:
                        card_indices_by_type['length'].append(idx)
                else:
                    if len(word) == req_len:
                        card_indices_by_type['length'].append(idx)
        
        for card_type in player.card_priority:
            if card_indices_by_type[card_type]:
                return card_indices_by_type[card_type][0]
        
        return None

    def set_card_priority(self, player_id: str, priority: List[str]):
        player = self.players.get(player_id)
        if player and set(priority) == {'char', 'row', 'length'} and len(priority) == 3:
            player.card_priority = priority

    def reroll(self, player_id: str) -> dict:
        if self.status != "playing":
            return {"success": False, "message": "ゲーム中ではありません"}

        player = self.players.get(player_id)
        if not player:
            return {"success": False, "message": "プレイヤーが見つかりません"}

        if len(self.deck) == 0:
            return {"success": False, "message": "山札が空です"}
        
        current_hand_size = len(player.hand)
        new_hand_size = current_hand_size + 1
        
        if len(self.deck) < new_hand_size:
            return {"success": False, "message": f"山札不足（必要: {new_hand_size}枚）"}
        
        self.deck.extend(player.hand)
        player.hand = []
        random.shuffle(self.deck)
        player.hand = [self.deck.pop() for _ in range(new_hand_size)]
        
        return {"success": True, "message": f"リロールしました（{new_hand_size}枚）"}

class GameManager:
    def __init__(self):
        self.rooms: Dict[str, WordBasketGame] = {}

    def create_room(self) -> str:
        room_code = str(random.randint(1000, 9999))
        while room_code in self.rooms:
            room_code = str(random.randint(1000, 9999))
        
        self.rooms[room_code] = WordBasketGame(room_code)
        return room_code

    def get_room(self, room_code: str) -> Optional[WordBasketGame]:
        return self.rooms.get(room_code)
