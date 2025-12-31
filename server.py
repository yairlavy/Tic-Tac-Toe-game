"""
Tic-Tac-Toe Game Server
Multi-client game server supporting multiple concurrent games
"""

import socket
import threading
import json
import time

# Server Configuration
HOST = '127.0.0.1'
PORT = 5000
FORMAT = 'utf-8'
ADDR = (HOST, PORT)
MESSAGE_DELIMITER = '\n<END>\n'

# Game state storage
games = {}  # {game_id: Game object}
game_id_counter = 0
games_lock = threading.Lock()


class Game:
    """Represents a single Tic-Tac-Toe game instance"""
    
    def __init__(self, game_id, num_players, creator_name):
        self.game_id = game_id
        self.num_players = num_players
        self.board_size = (num_players + 1) ** 2
        self.board = [' ' for _ in range(self.board_size)]
        self.players = []  # List of (conn, addr, name, symbol)
        self.current_player_idx = 0
        self.game_started = False
        self.game_over = False
        self.winner = None
        self.creator_name = creator_name
        self.symbols = ['X', 'O', '∆', '□', '◇', '★', '♦', '♣']
        self.lock = threading.Lock()
    
    def add_player(self, conn, addr, name):
        """Add a player to the game"""
        with self.lock:
            if len(self.players) >= self.num_players:
                return False, "Game is full"
            
            symbol = self.symbols[len(self.players)]
            self.players.append((conn, addr, name, symbol))
            
            if len(self.players) == self.num_players:
                self.game_started = True
            
            return True, symbol
    
    def get_board_dimension(self):
        """Get board dimensions (e.g., 3x3, 4x4)"""
        import math
        dim = int(math.sqrt(self.board_size))
        return dim
    
    def make_move(self, player_idx, position):
        """Make a move on the board"""
        with self.lock:
            if self.game_over:
                return False, "Game is over"
            
            if player_idx != self.current_player_idx:
                return False, "Not your turn"
            
            if position < 0 or position >= self.board_size:
                return False, "Invalid position"
            
            if self.board[position] != ' ':
                return False, "Position already occupied"
            
            symbol = self.players[player_idx][3]
            self.board[position] = symbol
            
            if self.check_winner(symbol):
                self.game_over = True
                self.winner = player_idx
                return True, "win"
            
            if self.check_draw():
                self.game_over = True
                return True, "draw"
            
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players
            return True, "continue"
    
    def check_winner(self, symbol):
        """Check if the given symbol has won (3 in a row)"""
        dim = self.get_board_dimension()
        
        # Check rows
        for row in range(dim):
            for col in range(dim - 2):
                idx = row * dim + col
                if (self.board[idx] == symbol and 
                    self.board[idx + 1] == symbol and 
                    self.board[idx + 2] == symbol):
                    return True
        
        # Check columns
        for col in range(dim):
            for row in range(dim - 2):
                idx = row * dim + col
                if (self.board[idx] == symbol and 
                    self.board[idx + dim] == symbol and 
                    self.board[idx + 2 * dim] == symbol):
                    return True
        
        # Check diagonals (top-left to bottom-right)
        for row in range(dim - 2):
            for col in range(dim - 2):
                idx = row * dim + col
                if (self.board[idx] == symbol and 
                    self.board[idx + dim + 1] == symbol and 
                    self.board[idx + 2 * (dim + 1)] == symbol):
                    return True
        
        # Check diagonals (top-right to bottom-left)
        for row in range(dim - 2):
            for col in range(2, dim):
                idx = row * dim + col
                if (self.board[idx] == symbol and 
                    self.board[idx + dim - 1] == symbol and 
                    self.board[idx + 2 * (dim - 1)] == symbol):
                    return True
        
        return False
    
    def check_draw(self):
        """Check if the game is a draw"""
        return ' ' not in self.board
    
    def get_board_str(self):
        """Get string representation of the board"""
        dim = self.get_board_dimension()
        lines = []
        
        # Column headers
        lines.append("\n     " + "   ".join(str(i) for i in range(dim)))
        lines.append("   +" + "---+" * dim)
        
        for row in range(dim):
            row_cells = []
            for col in range(dim):
                idx = row * dim + col
                cell = self.board[idx] if self.board[idx] != ' ' else ' '
                row_cells.append(f" {cell} ")
            lines.append(f" {row} |" + "|".join(row_cells) + "|")
            lines.append("   +" + "---+" * dim)
        
        # Position guide
        lines.append("\nPositions:")
        for row in range(dim):
            pos_cells = []
            for col in range(dim):
                idx = row * dim + col
                pos_cells.append(f"{idx:2d}")
            lines.append("  " + "  ".join(pos_cells))
        
        return "\n".join(lines)
    
    def get_game_state(self):
        """Get current game state as dictionary"""
        return {
            'game_id': self.game_id,
            'board': self.board,
            'board_str': self.get_board_str(),
            'current_player': self.current_player_idx,
            'game_started': self.game_started,
            'game_over': self.game_over,
            'winner': self.winner,
            'players': [(name, symbol) for _, _, name, symbol in self.players]
        }


def send_message(conn, message):
    """Send a message to a client with delimiter"""
    try:
        if isinstance(message, dict):
            message = json.dumps(message)
        message_with_delimiter = message + MESSAGE_DELIMITER
        conn.send(message_with_delimiter.encode(FORMAT))
        return True
    except:
        return False


def receive_message(conn):
    """Receive a message from a client"""
    try:
        data = conn.recv(4096).decode(FORMAT)
        if data:
            # Handle delimiter - take first complete message
            if MESSAGE_DELIMITER in data:
                data = data.split(MESSAGE_DELIMITER)[0]
            try:
                return json.loads(data)
            except:
                return data
        return None
    except:
        return None


def broadcast_game_state(game):
    """Send game state to all players in the game"""
    state = game.get_game_state()
    
    for idx, (conn, addr, name, symbol) in enumerate(game.players):
        msg = {
            'type': 'game_state',
            'state': state,
            'your_turn': idx == game.current_player_idx,
            'your_symbol': symbol
        }
        send_message(conn, msg)


def handle_game_client(conn, addr, game, player_idx):
    """Handle a client during gameplay"""
    try:
        while not game.game_over and game.players:
            # Wait for player's move
            data = receive_message(conn)
            
            if data is None:
                print(f"[GAME {game.game_id}] Player {player_idx} disconnected")
                break
            
            if isinstance(data, dict) and data.get('type') == 'move':
                position = data.get('position')
                success, result = game.make_move(player_idx, position)
                
                if success:
                    broadcast_game_state(game)
                    
                    if result == "win":
                        winner_name = game.players[game.winner][2]
                        time.sleep(0.1)  # Small delay to ensure state is received first
                        for p_conn, _, _, _ in game.players:
                            send_message(p_conn, {
                                'type': 'game_end',
                                'result': 'win',
                                'winner': winner_name
                            })
                        print(f"[GAME {game.game_id}] Winner: {winner_name}")
                        break
                    elif result == "draw":
                        time.sleep(0.1)  # Small delay to ensure state is received first
                        for p_conn, _, _, _ in game.players:
                            send_message(p_conn, {
                                'type': 'game_end',
                                'result': 'draw'
                            })
                        print(f"[GAME {game.game_id}] Draw!")
                        break
                else:
                    send_message(conn, {
                        'type': 'error',
                        'message': result
                    })
        
    except Exception as e:
        print(f"[ERROR] Game client handler: {e}")
    finally:
        print(f"[GAME {game.game_id}] Player {player_idx} handler ended")


def handle_client(conn, addr):
    """Handle a client connection"""
    print(f'[CLIENT CONNECTED] {addr}')
    
    try:
        # Get player name
        send_message(conn, {'type': 'request_name'})
        name_data = receive_message(conn)
        player_name = name_data.get('name', 'Unknown') if isinstance(name_data, dict) else 'Unknown'
        
        print(f"[CLIENT] {addr} identified as {player_name}")
        
        while True:
            # Send menu
            send_message(conn, {
                'type': 'menu',
                'message': 'Choose an option:\n1. Create new game\n2. List available games\n3. Join game\n4. Exit'
            })
            
            choice = receive_message(conn)
            
            if choice is None:
                break
            
            action = choice.get('action') if isinstance(choice, dict) else choice
            
            if action == '1' or action == 'create':
                # Create new game
                send_message(conn, {'type': 'request_players', 'message': 'Enter number of players (2-8):'})
                num_data = receive_message(conn)
                num_players = int(num_data.get('num_players', 2)) if isinstance(num_data, dict) else 2
                
                if num_players < 2 or num_players > 8:
                    send_message(conn, {'type': 'error', 'message': 'Invalid number of players'})
                    continue
                
                global game_id_counter
                with games_lock:
                    game_id = game_id_counter
                    game_id_counter += 1
                    game = Game(game_id, num_players, player_name)
                    games[game_id] = game
                
                success, symbol = game.add_player(conn, addr, player_name)
                
                send_message(conn, {
                    'type': 'game_created',
                    'game_id': game_id,
                    'symbol': symbol,
                    'message': f'Game {game_id} created! Waiting for {num_players - 1} more players...'
                })
                
                print(f"[GAME CREATED] Game {game_id} by {player_name}")
                
                # Wait for game to start
                while not game.game_started:
                    time.sleep(0.5)
                
                send_message(conn, {'type': 'game_start', 'message': 'Game starting!'})
                broadcast_game_state(game)
                
                # Handle gameplay
                player_idx = 0
                handle_game_client(conn, addr, game, player_idx)
                
                # Clean up game
                with games_lock:
                    if game_id in games:
                        del games[game_id]
                
                break
                
            elif action == '2' or action == 'list':
                # List available games
                with games_lock:
                    available = []
                    for gid, game in games.items():
                        if not game.game_started:
                            available.append({
                                'game_id': gid,
                                'creator': game.creator_name,
                                'players': f"{len(game.players)}/{game.num_players}",
                                'board_size': f"{game.get_board_dimension()}x{game.get_board_dimension()}"
                            })
                
                send_message(conn, {
                    'type': 'game_list',
                    'games': available
                })
                
            elif action == '3' or action == 'join':
                # Join existing game
                send_message(conn, {'type': 'request_game_id', 'message': 'Enter game ID to join:'})
                gid_data = receive_message(conn)
                game_id = int(gid_data.get('game_id', -1)) if isinstance(gid_data, dict) else -1
                
                with games_lock:
                    if game_id not in games:
                        send_message(conn, {'type': 'error', 'message': 'Game not found'})
                        continue
                    game = games[game_id]
                
                success, result = game.add_player(conn, addr, player_name)
                
                if not success:
                    send_message(conn, {'type': 'error', 'message': result})
                    continue
                
                symbol = result
                player_idx = len(game.players) - 1
                
                send_message(conn, {
                    'type': 'game_joined',
                    'game_id': game_id,
                    'symbol': symbol,
                    'message': f'Joined game {game_id}! You are {symbol}'
                })
                
                print(f"[GAME {game_id}] {player_name} joined")
                
                # Notify all players
                for p_conn, _, _, _ in game.players:
                    send_message(p_conn, {
                        'type': 'player_joined',
                        'message': f'{player_name} joined the game!'
                    })
                
                # Wait for game to start
                while not game.game_started:
                    time.sleep(0.5)
                
                send_message(conn, {'type': 'game_start', 'message': 'Game starting!'})
                broadcast_game_state(game)
                
                # Handle gameplay
                handle_game_client(conn, addr, game, player_idx)
                break
                
            elif action == '4' or action == 'exit':
                send_message(conn, {'type': 'goodbye', 'message': 'Goodbye!'})
                break
            
    except Exception as e:
        print(f"[ERROR] Client handler: {e}")
    finally:
        conn.close()
        print(f"[CLIENT DISCONNECTED] {addr}")


def start_server():
    """Start the Tic-Tac-Toe server"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(ADDR)
    
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    server_socket.listen()
    
    try:
        while True:
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            conn, addr = server_socket.accept()
            
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("\n[SHUTTING DOWN] Server shutting down...")
    finally:
        server_socket.close()


if __name__ == '__main__':
    print("[STARTING] Tic-Tac-Toe server is starting...")
    start_server()
    print("[STOPPED] Server stopped")
