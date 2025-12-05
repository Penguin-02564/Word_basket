from game import WordBasketGame, Card

def test_auto_select():
    game = WordBasketGame("test_room")
    
    # Mock hand
    game.hand = [
        Card("char", "た", "た"),
        Card("char", "ふ", "ふ"),
        Card("row", "かきくけこ", "か行"),
        Card("length", "5", "5文字")
    ]
    
    print("=== Auto Card Selection Test ===\n")
    
    # Test 1: Word ending with 'た' - should select char card (index 0)
    game.current_word = "テスト_あ"
    word1 = "あした"  # ends with 'た'
    idx1 = game.auto_select_card(word1)
    print(f"Test 1: '{word1}' (ends 'た')")
    print(f"  Selected card index: {idx1}")
    if idx1 is not None:
        print(f"  Card: {game.hand[idx1].display} ({game.hand[idx1].type})")
    print(f"  Expected: 0 (char 'た')")
    print(f"  Result: {'PASS' if idx1 == 0 else 'FAIL'}\n")
    
    # Test 2: Word ending with 'き' - should select row card (index 2)
    word2 = "あさき"  # ends with 'き'
    idx2 = game.auto_select_card(word2)
    print(f"Test 2: '{word2}' (ends 'き')")
    print(f"  Selected card index: {idx2}")
    if idx2 is not None:
        print(f"  Card: {game.hand[idx2].display} ({game.hand[idx2].type})")
    print(f"  Expected: 2 (row 'か行')")
    print(f"  Result: {'PASS' if idx2 == 2 else 'FAIL'}\n")
    
    # Test 3: 5-char word - should select length card (index 3)
    word3 = "あいうえお"  # 5 chars
    idx3 = game.auto_select_card(word3)
    print(f"Test 3: '{word3}' (5 chars)")
    print(f"  Selected card index: {idx3}")
    if idx3 is not None:
        print(f"  Card: {game.hand[idx3].display} ({game.hand[idx3].type})")
    print(f"  Expected: 3 (length '5')")
    print(f"  Result: {'PASS' if idx3 == 3 else 'FAIL'}\n")
    
    # Test 4: Change priority - row > char > length
    print("=== Test 4: Priority Change ===")
    game.set_card_priority(['row', 'char', 'length'])
    print(f"New priority: {game.card_priority}")
    
    # Same word as Test 2 - should still select row card
    idx4 = game.auto_select_card(word2)
    print(f"Word: '{word2}' (ends 'き')")
    print(f"  Selected card index: {idx4}")
    if idx4 is not None:
        print(f"  Card: {game.hand[idx4].display} ({game.hand[idx4].type})")
    print(f"  Expected: 2 (row 'か行' - now priority 1)")
    print(f"  Result: {'PASS' if idx4 == 2 else 'FAIL'}\n")
    
    # Test 5: Word with long vowel
    word5 = "スキー"  # ends 'ー' -> 'キ' -> 'き'
    idx5 = game.auto_select_card(word5)
    print(f"Test 5: '{word5}' (ends 'ー' -> 'キ')")
    print(f"  Selected card index: {idx5}")
    if idx5 is not None:
        print(f"  Card: {game.hand[idx5].display} ({game.hand[idx5].type})")
    print(f"  Expected: 2 (row 'か行')")
    print(f"  Result: {'PASS' if idx5 == 2 else 'FAIL'}\n")
    
    # Test 6: Word with dakuten
    word6 = "あしだ"  # ends 'だ' -> normalized 'た'
    idx6 = game.auto_select_card(word6)
    print(f"Test 6: '{word6}' (ends 'だ' -> normalized 'た')")
    print(f"  Selected card index: {idx6}")
    if idx6 is not None:
        print(f"  Card: {game.hand[idx6].display} ({game.hand[idx6].type})")
    # With priority ['row', 'char', 'length'], should select char (index 0)
    # because 'だ' normalizes to 'た' which matches char card
    print(f"  Expected: 0 (char 'た')")
    print(f"  Result: {'PASS' if idx6 == 0 else 'FAIL'}\n")
    
    # Test 7: No matching card
    word7 = "あしん"  # ends 'ん' - not allowed
    idx7 = game.auto_select_card(word7)
    print(f"Test 7: '{word7}' (ends 'ん' - no match)")
    print(f"  Selected card index: {idx7}")
    print(f"  Expected: None")
    print(f"  Result: {'PASS' if idx7 is None else 'FAIL'}\n")

if __name__ == "__main__":
    test_auto_select()
