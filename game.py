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
        self.status: str = "waiting" # waiting, playing, finished, finishing_check
        self.finished_players: List[Player] = []
        self.opposition_votes: Set[str] = set()
        self.pending_revert_state: Optional[dict] = None

        
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
        self.opposition_votes = set()
        self.pending_revert_state = None
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
            # Save state for potential revert if this is a finishing move
            # actually we might want to save it for ANY move if we wanted to allow undo, 
            # but requirement is specifically for "Oppose" on finishing move.
            
            previous_word = self.current_word
            played_card = player.hand[card_index]
            
            player.hand.pop(card_index)
            self.current_word = word
            
            message = "OK"
            game_over = False
            winner = None
            waiting_for_finish = False

            if len(player.hand) == 0:
                # Player finished - Enter Finishing Check
                self.status = "finishing_check"
                self.opposition_votes = set()
                self.pending_revert_state = {
                    "player_id": player_id,
                    "previous_word": previous_word,
                    "played_card": played_card,
                    "previous_rank": player.rank # Should be None
                }
                
                waiting_for_finish = True
                message = f"{player.name}さんが上がりました！反対があれば投票してください。"
                
                # We do NOT add to finished_players yet.
                # We wait for confirm_finish()
            
            return {
                "valid": True, 
                "message": message, 
                "game_over": game_over, 
                "waiting_for_finish": waiting_for_finish,
                "winner": None,
                "ranks": []
            }
        
        return {"valid": False, "message": "不明なエラー"}

    def oppose_move(self, voter_id: str) -> dict:
        if self.status != "finishing_check":
            return {"success": False, "message": "反対投票できるタイミングではありません"}
        
        if voter_id in self.opposition_votes:
            return {"success": False, "message": "既に投票済みです"}
            
        self.opposition_votes.add(voter_id)
        
        # Check majority
        # Active players = total players - finished players (who are already out/safe?)
        # Actually, everyone in the room should probably be able to vote? 
        # "过半数のプレイヤー" (Majority of players). Let's assume all players currently in game.
        active_player_count = len(self.players)
        if len(self.opposition_votes) > active_player_count / 2:
            self.revert_last_move()
            return {"success": True, "reverted": True, "message": "反対多数により却下されました！"}
            
        return {"success": True, "reverted": False, "message": "反対票を受け付けました"}

    def revert_last_move(self):
        if not self.pending_revert_state:
            return

        state = self.pending_revert_state
        player = self.players.get(state["player_id"])
        
        if player:
            player.hand.append(state["played_card"])
            # Reset rank just in case (though we didn't set it yet)
            player.rank = state["previous_rank"]
            
        self.current_word = state["previous_word"]
        self.status = "playing"
        self.pending_revert_state = None
        self.opposition_votes = set()

    def confirm_finish(self):
        if self.status != "finishing_check" or not self.pending_revert_state:
            return None

        state = self.pending_revert_state
        player = self.players.get(state["player_id"])
        
        if player:
            player.rank = len(self.finished_players) + 1
            self.finished_players.append(player)
            
            # Check if game should end
            active_players_count = len([p for p in self.players.values() if p.rank is None])
            
            game_over = False
            if active_players_count == 0:
                self.status = "finished"
                game_over = True
            elif active_players_count == 1 and len(self.players) > 1:
                last_player = next(p for p in self.players.values() if p.rank is None)
                last_player.rank = len(self.finished_players) + 1
                self.finished_players.append(last_player)
                self.status = "finished"
                game_over = True
            else:
                self.status = "playing" # Continue game for others
            
            self.pending_revert_state = None
            self.opposition_votes = set()
            
            return {
                "game_over": game_over,
                "winner": self.finished_players[0].name if self.finished_players else None,
                "ranks": [p.to_dict() for p in self.finished_players] if game_over else [],
                "finished_player": player.name,
                "rank": player.rank
            }
        return None

    def exchange_hand(self, player_id: str, card_index: int) -> dict:
        if self.status != "playing":
            return {"success": False, "message": "ゲーム中ではありません"}

        player = self.players.get(player_id)
        if not player:
            return {"success": False, "message": "プレイヤーが見つかりません"}

        if not (0 <= card_index < len(player.hand)):
            return {"success": False, "message": "無効なカードです"}

        # Logic:
        # 1. Selected card becomes new target (current_word = card.value)
        # 2. Return remaining hand to deck
        # 3. Draw old_hand_size + 1
        
        selected_card = player.hand.pop(card_index)
        
        # Use the card's value as the new "word" to determine next target
        # But wait, current_word usually is a full word. 
        # If I set current_word = "あ", then next target is "あ".
        # If card is "length", value is "3". 
        # "文字数と開始文字、終了文字さえ合っていればどんな文字列でも受け付けていたが..."
        # The user example: "Current word 'program', hand 'wa, shi, nu'. Select 'shi'. Next word starts with 'shi'."
        # So effectively, we simulate playing 'shi' but without forming a word?
        # Or we just force the next target char to be 'shi'.
        # Setting current_word = "Exchange_" + char seems appropriate to set the target.
        
        new_target_char = ""
        if selected_card.type == "char":
            new_target_char = selected_card.value
        elif selected_card.type == "row":
            # For row card, maybe pick random or allow any?
            # Usually row card means "ends with something in this row".
            # If we use it to SET the start, maybe we pick the first char or random?
            # User said "Select 'shi' (from hand)... Next word starts with 'shi'".
            # If I select 'ka-row', maybe next word must start with something from 'ka-row'?
            # Or just pick one? Let's pick a random one from the row to be safe/simple, or just set it as the constraint.
            # But get_target_char relies on current_word.
            # Let's set current_word to something that ends with the desired char.
            # But for row card, it's a set of chars.
            # Let's assume we just pick one for simplicity or if the user meant specific card.
            # "Select 'shi'". 'shi' is a char card.
            # If it's a row card, let's say 'ka-row', does it mean next word starts with 'ka', 'ki', etc?
            # Standard Word Basket rules for "Reset": usually you play a card to change the leading character.
            # If I play "ka-row", usually I'd have to play a word ending in ka-row.
            # But here we are FORCING the change.
            # Let's just pick the first char of the row or random.
            # Or better, let's make a special "Exchange" word.
            if len(selected_card.value) > 1:
                 # It's a row card or similar. 
                 # Let's pick random from it to be the new start char.
                 new_target_char = random.choice(selected_card.value)
            else:
                 new_target_char = selected_card.value
        elif selected_card.type == "length":
            # Length card doesn't have a char.
            # If used for exchange, what happens?
            # Maybe it doesn't change the character? Or random?
            # User example only mentioned char card.
            # Let's assume length card cannot be used for this, or just changes nothing but hand?
            # "Hand is returned... +1 card".
            # If I use length card, maybe I just want to refresh hand.
            # Let's keep current target if length card is used?
            # Or maybe disallow length card?
            # Let's allow it but keep current target.
            new_target_char = self.get_target_char()

        self.current_word = "リロード_" + new_target_char

        # Return remaining hand to deck
        self.deck.extend(player.hand)
        player.hand = []
        random.shuffle(self.deck)
        
        # Draw new hand (original size (which was len+1 before pop) + 1)
        # Wait, "Original hand size + 1".
        # If I had 3 cards. Selected 1. Remaining 2.
        # Original size 3. New size 4.
        # So I draw 4.
        
        old_hand_size = len(self.deck) - len(self.deck) + len(player.hand) + 1 # logic math is weird here because I already extended deck
        # Actually:
        # I popped 1. current player.hand is empty (I put them in deck).
        # I want to draw (old_size + 1).
        # old_size was (count of cards returned + 1 (the popped one)).
        # So if I returned 2 cards, old size was 3. I want 4.
        # So draw (returned_count + 2).
        
        cards_to_draw = len(self.deck) - len(self.deck) # 0? no.
        # Let's track count before extending.
        # actually I already extended.
        # Let's just pass the number.
        # I need to know how many cards were in hand BEFORE pop.
        # It was `len(player.hand)` (before extend) + 1 (the popped one).
        # Wait, I popped `selected_card` first.
        # So `len(player.hand)` is now `original - 1`.
        # I extended deck with `player.hand`.
        # So I need to draw `(original - 1) + 2` = `original + 1`.
        # So `len(cards_returned) + 2`.
        
        num_to_draw = 0 
        # Wait, I can't easily know how many I extended since I didn't count.
        # Let's rewrite slightly.
        
        pass # Placeholder to be overwritten by below logic

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

    def exchange_hand(self, player_id: str, card_index: int) -> dict:
        if self.status != "playing":
            return {"success": False, "message": "ゲーム中ではありません"}

        player = self.players.get(player_id)
        if not player:
            return {"success": False, "message": "プレイヤーが見つかりません"}

        if not (0 <= card_index < len(player.hand)):
            return {"success": False, "message": "無効なカードです"}

        # 1. Get selected card
        selected_card = player.hand.pop(card_index)
        original_hand_size = len(player.hand) + 1

        # 2. Determine new target
        new_target_char = ""
        if selected_card.type == "char":
            new_target_char = selected_card.value
        elif selected_card.type == "row":
            # Pick random char from row
            new_target_char = random.choice(selected_card.value)
        elif selected_card.type == "length":
            # Keep current target
            new_target_char = self.get_target_char()

        self.current_word = "リロード_" + new_target_char

        # 3. Return remaining hand to deck
        self.deck.extend(player.hand)
        player.hand = []
        random.shuffle(self.deck)
        
        # 4. Draw new hand (original + 1)
        num_to_draw = original_hand_size + 1
        
        if len(self.deck) < num_to_draw:
             # Not enough cards? Just draw what we can.
             num_to_draw = len(self.deck)
        
        player.hand = [self.deck.pop() for _ in range(num_to_draw)]
        
        return {"success": True, "message": f"手札を交換しました（{num_to_draw}枚）"}

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
