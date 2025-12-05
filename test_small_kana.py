from game import WordBasketGame, Card

def test_small_kana_and_last_card():
    game = WordBasketGame("test_room")
    
    print("=== Test 1: Small ya/yu/yo handling ===")
    
    # Test with word ending in small "ょ" (yo)
    game.current_word = "きょうはいいてんき_ょ"
    target = game.get_target_char()
    print(f"Word ending in 'ょ': {game.current_word}")
    print(f"Target char: {target}")
    print(f"Expected: よ")
    print(f"Result: {'PASS' if target == 'よ' else 'FAIL'}\n")
    
    # Test with word ending in small "ゃ" (ya)
    game.current_word = "テストちゃ"
    target = game.get_target_char()
    print(f"Word ending in 'ゃ': {game.current_word}")
    print(f"Target char: {target}")
    print(f"Expected: や")
    print(f"Result: {'PASS' if target == 'や' else 'FAIL'}\n")
    
    # Test with word ending in small "ゅ" (yu)
    game.current_word = "テストしゅ"
    target = game.get_target_char()
    print(f"Word ending in 'ゅ': {game.current_word}")
    print(f"Target char: {target}")
    print(f"Expected: ゆ")
    print(f"Result: {'PASS' if target == 'ゆ' else 'FAIL'}\n")
    
    print("=== Test 2: Minimum length for last card ===")
    
    # Mock a hand with multiple cards
    game.hand = [
        Card("char", "た", "た"),
        Card("char", "ふ", "ふ")
    ]
    game.current_word = "テスト_あ"
    
    # Should accept 3-char word when hand has 2 cards
    result = game.check_move("あした", 0)  # 3 characters
    print(f"Hand: 2 cards, Word: 'あした' (3 chars)")
    print(f"Valid: {result['valid']}")
    print(f"Expected: True")
    print(f"Result: {'PASS' if result['valid'] else 'FAIL'}\n")
    
    # Test with 1 card - setup current word to end with "あ"
    game.hand = [Card("char", "た", "た")]
    game.current_word = "テスト_あ"
    
    # Should reject 3-char word when hand has 1 card
    result = game.check_move("あした", 0)  # 3 characters, "あした" ends with "た"
    print(f"Hand: 1 card, Word: 'あした' (3 chars)")
    print(f"Valid: {result['valid']}")
    print(f"Message: {result.get('message', '')}")
    print(f"Expected: False (requires 4+ characters)")
    print(f"Result: {'PASS' if not result['valid'] and '4' in result.get('message', '') else 'FAIL'}\n")
    
    # Should accept 4-char word when hand has 1 card
    result = game.check_move("あしたた", 0)  # 4 characters, ends with "た"
    print(f"Hand: 1 card, Word: 'あしたた' (4 chars)")
    print(f"Valid: {result['valid']}")
    print(f"Message: {result.get('message', '')}")
    print(f"Expected: True")
    print(f"Result: {'PASS' if result['valid'] else 'FAIL'}\n")
    
    print("=== Test 3: Combined test (small kana + last card) ===")
    
    game.current_word = "テストちゃ"  # Ends with "ちゃ" -> target will be "や"
    game.hand = [Card("char", "や", "や")]
    
    # 4-char word starting with "や" (target from "ちゃ"), ends with "や"
    result = game.check_move("やすみや", 0)  # 4 characters, starts "や", ends "や"
    print(f"Current word ends in 'ゃ' (target: 'や'), Hand: 1 card (や)")
    print(f"Word: 'やすみや' (4 chars, starts 'や', ends 'や')")
    print(f"Valid: {result['valid']}")
    print(f"Message: {result.get('message', '')}")
    print(f"Expected: True")
    print(f"Result: {'PASS' if result['valid'] else 'FAIL'}\n")
    
    # 3-char word should fail (too short for last card)
    result = game.check_move("やすや", 0)  # 3 characters
    print(f"Word: 'やすや' (3 chars, starts 'や', ends 'や')")
    print(f"Valid: {result['valid']}")
    print(f"Message: {result.get('message', '')}")
    print(f"Expected: False (requires 4+ characters)")
    print(f"Result: {'PASS' if not result['valid'] and '4' in result.get('message', '') else 'FAIL'}\n")

if __name__ == "__main__":
    test_small_kana_and_last_card()
