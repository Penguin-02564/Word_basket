import unittest
from game import WordBasketGame

class TestLongVowelLogic(unittest.TestCase):
    def setUp(self):
        self.game = WordBasketGame("test_room")
        
    def test_long_vowel_target_ta(self):
        # たーみねーたー -> たー ends with ー, prev is た -> vowel 'a' -> あ
        self.game.current_word = "たー"
        target = self.game.get_target_char()
        self.assertEqual(target, "あ")
    
    def test_long_vowel_target_ki(self):
        # きー -> きー ends with ー, prev is き -> vowel 'i' -> い
        self.game.current_word = "きー"
        target = self.game.get_target_char()
        self.assertEqual(target, "い")
    
    def test_long_vowel_target_su(self):
        # すー -> すー ends with ー, prev is す -> vowel 'u' -> う
        self.game.current_word = "すー"
        target = self.game.get_target_char()
        self.assertEqual(target, "う")
    
    def test_long_vowel_target_te(self):
        # てー -> てー ends with ー, prev is て -> vowel 'e' -> え
        self.game.current_word = "てー"
        target = self.game.get_target_char()
        self.assertEqual(target, "え")
    
    def test_long_vowel_target_ko(self):
        # こー -> こー ends with ー, prev is こ -> vowel 'o' -> お
        self.game.current_word = "こー"
        target = self.game.get_target_char()
        self.assertEqual(target, "お")
    
    def test_no_long_vowel(self):
        # Regular word without long vowel
        self.game.current_word = "ねこ"
        target = self.game.get_target_char()
        self.assertEqual(target, "こ")

if __name__ == '__main__':
    unittest.main()
