from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from game import WordBasketGame, GameManager
import os
import json
import uuid
import asyncio
from typing import Dict, List

app = FastAPI()

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Game Manager instance
game_manager = GameManager()

class ConnectionManager:
    def __init__(self):
        # room_code -> {player_id -> WebSocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_code: str, player_id: str):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = {}
        self.active_connections[room_code][player_id] = websocket

    def disconnect(self, room_code: str, player_id: str):
        if room_code in self.active_connections:
            if player_id in self.active_connections[room_code]:
                del self.active_connections[room_code][player_id]
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict, room_code: str):
        if room_code in self.active_connections:
            for connection in self.active_connections[room_code].values():
                try:
                    await connection.send_json(message)
                except Exception:
                    # Handle potential broken pipe
                    pass

manager = ConnectionManager()

# API Models
class CreateRoomResponse(BaseModel):
    room_code: str

# Health check endpoint for Render
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Root endpoint
@app.get("/api")
def api_root():
    return {"message": "Word Basket API is running"}

@app.post("/api/rooms")
def create_room():
    room_code = game_manager.create_room()
    return {"room_code": room_code}

@app.websocket("/ws/{room_code}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_name: str, player_id: str = None):
    # Check if room exists
    game = game_manager.get_room(room_code)
    if not game:
        await websocket.close(code=4000, reason="Room not found")
        return

    # Handle player_id logic
    is_reconnect = False
    if player_id and player_id in game.players:
        # Reconnection
        player = game.players[player_id]
        is_reconnect = True
    else:
        # New player
        player_id = str(uuid.uuid4())
        player = game.add_player(player_id, player_name)
    
    # Join room (ConnectionManager handles overwriting existing connection if any)
    await manager.connect(websocket, room_code, player_id)
    
    try:
        # Broadcast room update
        msg = f"{player.name}さんが再接続しました" if is_reconnect else f"{player.name}さんが参加しました"
        
        # If game is finished, send game_over and ranks
        if game.status == "finished":
            await broadcast_game_state(
                game, 
                room_code, 
                message=msg, 
                game_over=True, 
                winner=game.finished_players[0].name if game.finished_players else None,
                ranks=[p.to_dict() for p in game.finished_players]
            )
        else:
            await broadcast_game_state(game, room_code, message=msg)
        
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "start_game":
                if player.is_host:
                    game.start_game()
                    await broadcast_game_state(game, room_code, message=f"{player.name}さんがゲームを開始しました！")
                else:
                    await manager.send_personal_message({"type": "error", "message": "ホストのみがゲームを開始できます"}, websocket)
            
            elif action == "play_word":
                word = data.get("word")
                card_index = data.get("card_index")
                
                # Auto-select logic if needed (can be implemented on client or server)
                if card_index == -1:
                    card_index = game.auto_select_card(player_id, word)
                    if card_index is None:
                        await manager.send_personal_message({"type": "error", "message": "この単語に使えるカードがありません"}, websocket)
                        continue

                result = game.check_move(player_id, word, card_index)
                
                if result["valid"]:
                    msg = f"{player.name}さんが「{word}」を出しました！"
                    
                    if result.get("waiting_for_finish"):
                        # Broadcast "Finishing Check" state - wait for approval/rejection
                        await broadcast_game_state(game, room_code, message=msg)
                        
                        # Start 10-second timeout
                        asyncio.create_task(voting_timeout(game, room_code, 10))
                    elif result.get("game_over"):
                        # Should not happen with new logic, but keep for safety
                        msg = f"{player.name}さんがクリアしました！勝者: {player.name}"
                        await broadcast_game_state(game, room_code, message=msg, game_over=True, winner=player.name, ranks=result.get("ranks", []))
                    else:
                        await broadcast_game_state(game, room_code, message=msg)
                else:
                    await manager.send_personal_message({"type": "error", "message": result["message"]}, websocket)
            
            elif action == "approve":
                result = game.approve_finish(player_id)
                if result["success"]:
                    if result.get("all_voted"):
                        if result.get("approved"):
                            # All voted and approved - finalize
                            finish_result = game.confirm_finish()
                            if finish_result:
                                msg = f"{finish_result['finished_player']}さんが{finish_result['rank']}位で確定しました！"
                                
                                # Debug log
                                print(f"[DEBUG] confirm_finish result: game_over={finish_result['game_over']}, status={game.status}, ranks={finish_result['ranks']}")
                                
                                if finish_result['game_over']:
                                    # Game is over - show results
                                    msg += f" ゲーム終了！"
                                    await broadcast_game_state(
                                        game, 
                                        room_code, 
                                        message=msg, 
                                        game_over=True, 
                                        winner=finish_result['winner'], 
                                        ranks=finish_result['ranks']
                                    )
                                else:
                                    # Game continues with remaining players
                                    msg += " ゲームを続けます。"
                                    await broadcast_game_state(game, room_code, message=msg)
                        else:
                            # Rejected
                            await broadcast_game_state(game, room_code, message=result["message"])
                    else:
                        # Not all voted yet
                        await broadcast_game_state(game, room_code, message=f"{player.name}さんが承諾しました")
                else:
                    await manager.send_personal_message({"type": "error", "message": result["message"]}, websocket)
            
            elif action == "reroll":
                # Now acts as "exchange_hand"
                card_index = data.get("card_index")
                if card_index is None or card_index == -1:
                     # If client didn't send index (old client?), try to use auto-select or fail
                     # But UI should enforce it.
                     await manager.send_personal_message({"type": "error", "message": "交換するカードを選択してください"}, websocket)
                     continue

                result = game.exchange_hand(player_id, card_index)
                if result["success"]:
                    await broadcast_game_state(game, room_code, message=f"{player.name}さんが手札を交換しました")
                else:
                    await manager.send_personal_message({"type": "error", "message": result["message"]}, websocket)
            
            elif action == "oppose":
                result = game.oppose_move(player_id)
                if result["success"]:
                    msg = result["message"]
                    if result.get("reverted"):
                        msg = "拒否多数により、前の手が却下されました！"
                    await broadcast_game_state(game, room_code, message=msg)
                else:
                    await manager.send_personal_message({"type": "error", "message": result["message"]}, websocket)

            elif action == "set_priority":
                priority = data.get("priority")
                game.set_card_priority(player_id, priority)
                # No broadcast needed, just personal update maybe?
                await broadcast_game_state(game, room_code) # Update to reflect priority if we send it back
            
            elif action == "get_hand":
                target_id = data.get("target_id")
                if not target_id:
                    await manager.send_personal_message({"type": "error", "message": "対象プレイヤーが指定されていません"}, websocket)
                else:
                    result = game.get_opponent_hand(player_id, target_id)
                    if result["success"]:
                        await manager.send_personal_message({
                            "type": "view_hand",
                            "target_name": result["target_name"],
                            "hand": result["hand"]
                        }, websocket)
                    else:
                        await manager.send_personal_message({"type": "error", "message": result["message"]}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(room_code, player_id)
        
        if player.is_host:
            # Host disconnected, end the game for everyone
            await manager.broadcast({
                "type": "return_to_title",
                "message": "ホストが切断しました。タイトルに戻ります。"
            }, room_code)
            # Optionally clean up the room immediately or let it be
            # For now, we just notify everyone.
        else:
            # Normal player disconnected
            await broadcast_game_state(game, room_code, message=f"{player.name}さんが切断しました")

async def voting_timeout(game: WordBasketGame, room_code: str, timeout_seconds: int):
    """Wait for timeout and force voting decision if still in finishing_check."""
    await asyncio.sleep(timeout_seconds)
    
    # Check if still in finishing_check (voting might have already completed)
    if game.status == "finishing_check":
        # Force decision based on current votes
        finishing_player_id = game.pending_revert_state.get("player_id") if game.pending_revert_state else None
        active_players = [pid for pid in game.players.keys() if pid != finishing_player_id and game.players[pid].rank is None]
        
        approvals = len(game.approval_votes)
        rejections = len(game.opposition_votes)
        total_votes = approvals + rejections
        
        # Decision: approve if >= 50% of votes are approvals
        if total_votes > 0:
            if approvals >= total_votes / 2:
                # Approve
                finish_result = game.confirm_finish()
                if finish_result:
                    msg = f"投票時間終了。{finish_result['finished_player']}さんが{finish_result['rank']}位で確定しました！"
                    
                    # Debug log
                    print(f"[DEBUG] voting_timeout (approved): game_over={finish_result['game_over']}, status={game.status}, ranks={finish_result['ranks']}")
                    
                    if finish_result['game_over']:
                        msg += " ゲーム終了！"
                        await broadcast_game_state(
                            game, 
                            room_code, 
                            message=msg, 
                            game_over=True, 
                            winner=finish_result['winner'], 
                            ranks=finish_result['ranks']
                        )
                    else:
                        msg += " ゲームを続けます。"
                        await broadcast_game_state(game, room_code, message=msg)
            else:
                # Reject
                game.revert_last_move()
                await broadcast_game_state(game, room_code, message="投票時間終了。拒否多数により却下されました")
        else:
            # No votes - default to approve
            finish_result = game.confirm_finish()
            if finish_result:
                msg = f"投票なし。{finish_result['finished_player']}さんが{finish_result['rank']}位で確定しました！"
                
                # Debug log
                print(f"[DEBUG] voting_timeout (no votes): game_over={finish_result['game_over']}, status={game.status}, ranks={finish_result['ranks']}")
                
                if finish_result['game_over']:
                    msg += " ゲーム終了！"
                    await broadcast_game_state(
                        game, 
                        room_code, 
                        message=msg, 
                        game_over=True, 
                        winner=finish_result['winner'], 
                        ranks=finish_result['ranks']
                    )
                else:
                    msg += " ゲームを続けます。"
                    await broadcast_game_state(game, room_code, message=msg)

async def broadcast_game_state(game: WordBasketGame, room_code: str, message: str = None, game_over: bool = False, winner: str = None, ranks: list = None):
    # Construct state for each player
    # We need to send personalized state (own hand) + public state (others' hand counts)
    
    # Calculate active voting players (exclude finishing player and finished players)
    finishing_player_id = game.pending_revert_state.get("player_id") if game.pending_revert_state else None
    active_voting_players = len([pid for pid in game.players.keys() 
                                  if pid != finishing_player_id and game.players[pid].rank is None])
    
    common_state = {
        "type": "game_state",
        "room_code": room_code,
        "status": game.status,
        "current_word": game.current_word,
        "target_char": game.get_target_char(),
        "deck_count": len(game.deck),
        "discard_pile_count": len(game.discard_pile),  # デバッグ用
        "dictionary_size": len(game.dictionary),
        "message": message,
        "game_over": game_over,
        "winner": winner,
        "ranks": ranks or [],
        "opposition_votes": len(game.opposition_votes),
        "approval_votes": len(game.approval_votes),
        "active_players": len(game.players),
        "active_voting_players": active_voting_players,
        "finishing_player_id": finishing_player_id
    }
    
    # Players info (public)
    players_info = []
    active_players = manager.active_connections.get(room_code, {})
    
    for p in game.players.values():
        p_dict = p.to_dict()
        p_dict["is_connected"] = p.player_id in active_players
        players_info.append(p_dict)
    common_state["players_info"] = players_info

    if room_code in manager.active_connections:
        for player_id, ws in manager.active_connections[room_code].items():
            player = game.players.get(player_id)
            if player:
                # Personal state
                personal_state = common_state.copy()
                personal_state["my_hand"] = [c.to_dict() for c in player.hand]
                personal_state["my_player_id"] = player_id
                personal_state["is_host"] = player.is_host
                personal_state["my_priority"] = player.card_priority
                personal_state["has_voted"] = player_id in game.approval_votes or player_id in game.opposition_votes
                
                try:
                    await ws.send_json(personal_state)
                except Exception:
                    pass

# Get the directory of the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Serve static files
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import socket
    
    def get_local_ip():
        try:
            # Connect to an external server (doesn't actually send data) to get the local IP used for routing
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    local_ip = get_local_ip()
    print("="*50)
    print(f"Server starting...")
    print(f"Local Access: http://localhost:8000")
    print(f"Network Access: http://{local_ip}:8000")
    print("="*50)
    
    # Use string reference for app to avoid some pickling issues on Windows if reload is used (though not used here)
    # But passing app instance is fine for simple usage.
    try:
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except OSError as e:
        print(f"Error starting server: {e}")
        print("Port 8000 might be in use. Please stop other python processes.")
