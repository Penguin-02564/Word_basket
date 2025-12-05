from game import WordBasketGame, Card, Player

def test_game_continuation_and_ranking():
    game = WordBasketGame("test_room")
    
    # Setup 3 players
    p1 = game.add_player("p1", "Player 1")
    p2 = game.add_player("p2", "Player 2")
    p3 = game.add_player("p3", "Player 3")
    
    game.start_game()
    
    # Mock hands for easy winning
    # Let's say target is 'あ'
    game.current_word = "ゲーム開始_あ"
    
    # P1 has 1 card 'い'
    p1.hand = [Card("char", "い", "い")]
    
    # P2 has 2 cards
    p2.hand = [Card("char", "う", "う"), Card("char", "え", "え")]
    
    # P3 has 3 cards
    p3.hand = [Card("char", "お", "お"), Card("char", "か", "か"), Card("char", "き", "き")]
    
    # P1 plays 'あい' and finishes
    result = game.check_move("p1", "あい", 0)
    
    assert result["valid"] == True
    assert result["game_over"] == False
    assert p1.rank == 1
    assert p1 in game.finished_players
    assert game.status == "playing"
    
    # P2 plays 'いう'
    # Current word is 'あい' -> ends with 'い'
    result = game.check_move("p2", "いう", 0)
    assert result["valid"] == True
    assert result["game_over"] == False
    assert p2.rank is None
    
    # P2 plays 'うえ' and finishes
    # Current word is 'いう' -> ends with 'う'
    result = game.check_move("p2", "うえ", 0)
    assert result["valid"] == True
    assert result["game_over"] == True # Should be over because only P3 is left
    assert p2.rank == 2
    assert p2 in game.finished_players
    assert game.status == "finished"
    
    # P3 should be automatically ranked last (3rd)
    assert p3.rank == 3
    assert p3 in game.finished_players
    assert game.finished_players == [p1, p2, p3]
    
    # Check result data
    assert result["winner"] == "Player 1" # First place is the winner
    assert len(result["ranks"]) == 3
    assert result["ranks"][0]["name"] == "Player 1"
    assert result["ranks"][0]["rank"] == 1
    assert result["ranks"][1]["name"] == "Player 2"
    assert result["ranks"][1]["rank"] == 2
    assert result["ranks"][2]["name"] == "Player 3"
    assert result["ranks"][2]["rank"] == 3

def test_two_player_game_end():
    game = WordBasketGame("test_room_2")
    p1 = game.add_player("p1", "Player 1")
    p2 = game.add_player("p2", "Player 2")
    
    game.start_game()
    game.current_word = "ゲーム開始_あ"
    
    p1.hand = [Card("char", "い", "い")]
    p2.hand = [Card("char", "う", "う")]
    
    # P1 finishes
    result = game.check_move("p1", "あい", 0)
    
    # Should end immediately because only 1 player left
    assert result["valid"] == True
    assert result["game_over"] == True
    assert p1.rank == 1
    assert p2.rank == 2
    assert game.status == "finished"
