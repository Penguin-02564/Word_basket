import unittest
from game import WordBasketGame, Card

class TestNewFeatures(unittest.TestCase):
    def setUp(self):
        self.game = WordBasketGame("test_room")
        self.p1 = self.game.add_player("p1", "Player 1")
        self.p2 = self.game.add_player("p2", "Player 2")
        self.p3 = self.game.add_player("p3", "Player 3")
        self.game.start_game()

    def test_exchange_hand(self):
        # Setup hand
        self.p1.hand = [Card("char", "あ", "あ"), Card("char", "い", "い")]
        original_len = len(self.p1.hand)
        
        # Select first card ("あ") to exchange
        # current_word should change to "リロード_あ"
        result = self.game.exchange_hand("p1", 0)
        
        self.assertTrue(result["success"])
        self.assertTrue(self.game.current_word.startswith("リロード_"))
        self.assertTrue(self.game.current_word.endswith("あ"))
        
        # Hand size should be original (2) + 1 = 3?
        # Wait, original hand size was 2.
        # Logic: pop 1 (remains 1). Return 1 to deck.
        # Draw (original_hand_size + 1) = 3.
        self.assertEqual(len(self.p1.hand), 3)

    def test_finishing_check_and_oppose(self):
        # Setup p1 to have 1 card
        target_char = self.game.get_target_char()
        # Need a word starting with target_char and ending with something we have.
        # Let's say target is 'あ'. We want to play 'あいいい'. Ends with 'い'.
        # So we need a card 'い'.
        
        # But wait, get_target_char might be random.
        # Let's force current_word to known.
        self.game.current_word = "ゲーム開始_あ"
        target_char = "あ"
        
        winning_card = Card("char", "い", "い")
        self.p1.hand = [winning_card]
        
        # Play "あいいい" (starts with あ, ends with い, length 4)
        result = self.game.check_move("p1", "あいいい", 0)
        
        self.assertTrue(result["valid"])
        self.assertTrue(result["waiting_for_finish"])
        self.assertEqual(self.game.status, "finishing_check")
        self.assertEqual(len(self.p1.hand), 0)
        
        # Oppose by p2
        vote_res = self.game.oppose_move("p2")
        self.assertTrue(vote_res["success"])
        self.assertFalse(vote_res["reverted"]) # 1/3 votes (3 players) -> not majority (> 1.5)
        
        # Oppose by p3 -> Majority (2/3)
        vote_res = self.game.oppose_move("p3")
        self.assertTrue(vote_res["success"])
        self.assertTrue(vote_res["reverted"])
        
        # Verify reversion
        self.assertEqual(self.game.status, "playing")
        self.assertEqual(len(self.p1.hand), 1)
        self.assertEqual(self.p1.hand[0].value, "い")

    def test_confirm_finish(self):
        # Setup p1 to have 1 card
        self.game.current_word = "ゲーム開始_あ"
        winning_card = Card("char", "い", "い")
        self.p1.hand = [winning_card]
        
        # Play winning card
        self.game.check_move("p1", "あいいい", 0)
        self.assertEqual(self.game.status, "finishing_check")
        self.assertEqual(self.game.status, "finishing_check")
        
        # Confirm finish
        res = self.game.confirm_finish()
        
        self.assertIsNotNone(res)
        self.assertEqual(res["finished_player"], "Player 1")
        self.assertIn(self.p1, self.game.finished_players)
        # Game continues for p2 and p3
        self.assertEqual(self.game.status, "playing") 

if __name__ == '__main__':
    unittest.main()
