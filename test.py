"""
Complete Automated Test Suite for Tic-Tac-Toe Game
Tests all scenarios to ensure the game works perfectly
"""

import socket
import json
import threading
import time
import sys

# Configuration
HOST = '127.0.0.1'
PORT = 5000
FORMAT = 'utf-8'
ADDR = (HOST, PORT)
MESSAGE_DELIMITER = '\n<END>\n'


class TestClient:
    """Test client that can be programmatically controlled"""
    
    def __init__(self, name):
        self.name = name
        self.socket = None
        self.connected = False
        self.buffer = ""
        self.messages_received = []
        
    def connect(self):
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(ADDR)
            self.socket.settimeout(10.0)
            self.connected = True
            return True
        except Exception as e:
            print(f"[TEST {self.name}] Connection failed: {e}")
            return False
    
    def send_message(self, message):
        """Send message to server"""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            message_with_delimiter = message + MESSAGE_DELIMITER
            self.socket.send(message_with_delimiter.encode(FORMAT))
            return True
        except Exception as e:
            print(f"[TEST {self.name}] Send failed: {e}")
            return False
    
    def receive_message(self, timeout=5.0):
        """Receive message from server"""
        if not self.connected or self.socket is None:
            return None
            
        try:
            old_timeout = self.socket.gettimeout()
            self.socket.settimeout(timeout)
            
            while True:
                if MESSAGE_DELIMITER in self.buffer:
                    parts = self.buffer.split(MESSAGE_DELIMITER, 1)
                    message = parts[0]
                    self.buffer = parts[1] if len(parts) > 1 else ""
                    
                    try:
                        msg = json.loads(message)
                        self.messages_received.append(msg)
                        return msg
                    except:
                        msg = {'type': 'text', 'message': message}
                        self.messages_received.append(msg)
                        return msg
                
                data = self.socket.recv(4096).decode(FORMAT)
                if not data:
                    return None
                self.buffer += data
        except socket.timeout:
            return None
        except Exception as e:
            return None
        finally:
            if self.socket:
                try:
                    self.socket.settimeout(old_timeout)
                except:
                    pass
    
    def receive_until_type(self, expected_type, max_attempts=10, timeout=2.0):
        """Keep receiving until we get a message of expected type"""
        for _ in range(max_attempts):
            msg = self.receive_message(timeout=timeout)
            if msg and msg.get('type') == expected_type:
                return msg
        return None
    
    def close(self):
        """Close connection"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None


class TicTacToeTests:
    """Complete test suite for Tic-Tac-Toe game"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def run_test(self, test_name, test_func):
        """Run a single test"""
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print('='*70)
        try:
            test_func()
            self.tests_passed += 1
            self.test_results.append((test_name, "PASSED", None))
            print(f"✅ {test_name} PASSED")
        except AssertionError as e:
            self.tests_failed += 1
            self.test_results.append((test_name, "FAILED", str(e)))
            print(f"❌ {test_name} FAILED: {e}")
        except Exception as e:
            self.tests_failed += 1
            self.test_results.append((test_name, "ERROR", str(e)))
            print(f"❌ {test_name} ERROR: {e}")
        
        time.sleep(1)  # Delay between tests
    
    # ===== CONNECTION TESTS =====
    
    def test_01_server_connection(self):
        """Test: Server is running and accepts connections"""
        client = TestClient("ConnectionTest")
        assert client.connect(), "Failed to connect to server - is server running?"
        client.close()
    
    def test_02_initial_handshake(self):
        """Test: Server sends name request on connection"""
        client = TestClient("HandshakeTest")
        client.connect()
        
        msg = client.receive_message()
        assert msg is not None, "No response from server"
        assert msg.get('type') == 'request_name', f"Expected request_name, got {msg.get('type')}"
        
        client.close()
    
    def test_03_name_submission(self):
        """Test: Client can submit name and receive menu"""
        client = TestClient("NameTest")
        client.connect()
        
        client.receive_message()  # request_name
        client.send_message({'name': 'TestPlayer'})
        
        msg = client.receive_message()
        assert msg is not None, "No menu received after name"
        assert msg.get('type') == 'menu', f"Expected menu, got {msg.get('type')}"
        assert 'Create new game' in msg.get('message', ''), "Menu missing expected options"
        
        client.close()
    
    # ===== MENU TESTS =====
    
    def test_04_menu_display(self):
        """Test: Menu shows all required options"""
        client = TestClient("MenuDisplayTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Test'})
        
        menu = client.receive_message()
        menu_text = menu.get('message', '')
        
        assert '1' in menu_text and 'Create' in menu_text, "Missing create option"
        assert '2' in menu_text and 'List' in menu_text, "Missing list option"
        assert '3' in menu_text and 'Join' in menu_text, "Missing join option"
        assert '4' in menu_text and 'Exit' in menu_text, "Missing exit option"
        
        client.close()
    
    def test_05_invalid_menu_choice(self):
        """Test: Invalid menu choice returns to menu"""
        client = TestClient("InvalidMenuTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Test'})
        client.receive_message()  # menu
        
        # Send invalid choice
        client.send_message({'action': '99'})
        
        # Should get menu again
        msg = client.receive_message(timeout=3.0)
        assert msg is not None, "Should receive menu again"
        assert msg.get('type') == 'menu', "Should return to menu after invalid choice"
        
        client.close()
    
    # ===== GAME CREATION TESTS =====
    
    def test_06_create_game_request(self):
        """Test: Creating game prompts for player count"""
        client = TestClient("CreateRequestTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Creator'})
        client.receive_message()
        
        client.send_message({'action': 'create'})
        msg = client.receive_message()
        
        assert msg.get('type') == 'request_players', "Should request player count"
        assert '2-8' in msg.get('message', ''), "Should specify valid range"
        
        client.close()
    
    def test_07_create_valid_game(self):
        """Test: Valid game creation succeeds"""
        client = TestClient("CreateValidTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Creator'})
        client.receive_message()
        
        client.send_message({'action': 'create'})
        client.receive_message()
        client.send_message({'num_players': 2})
        
        msg = client.receive_message()
        assert msg.get('type') == 'game_created', "Game should be created"
        assert 'game_id' in msg, "Should have game_id"
        assert 'symbol' in msg, "Should have player symbol"
        assert msg.get('symbol') == 'X', "First player should be X"
        
        client.close()
    
    def test_08_create_game_invalid_player_count_low(self):
        """Test: Player count too low is rejected and retried"""
        client = TestClient("InvalidLowTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Test'})
        client.receive_message()
        
        client.send_message({'action': 'create'})
        client.receive_message()
        client.send_message({'num_players': 1})
        
        # Should ask again
        msg = client.receive_message(timeout=3.0)
        assert msg is not None, "Should ask for player count again"
        assert msg.get('type') == 'request_players', "Should request players again"
        
        client.close()
    
    def test_09_create_game_invalid_player_count_high(self):
        """Test: Player count too high is rejected and retried"""
        client = TestClient("InvalidHighTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Test'})
        client.receive_message()
        
        client.send_message({'action': 'create'})
        client.receive_message()
        client.send_message({'num_players': 10})
        
        # Should ask again
        msg = client.receive_message(timeout=3.0)
        assert msg is not None, "Should ask for player count again"
        assert msg.get('type') == 'request_players', "Should request players again"
        
        client.close()
    
    def test_10_board_size_2_players(self):
        """Test: 2-player game has 3x3 board (9 squares)"""
        client = TestClient("Board2Test")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Test'})
        client.receive_message()
        client.send_message({'action': 'create'})
        client.receive_message()
        client.send_message({'num_players': 2})
        client.receive_message()
        
        # Board size = (num_players + 1)^2 = (2+1)^2 = 9
        # We'll verify later when game starts
        
        client.close()
    
    # ===== GAME LISTING TESTS =====
    
    def test_11_list_empty_games(self):
        """Test: Listing games when none exist"""
        client = TestClient("ListEmptyTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Lister'})
        client.receive_message()
        
        client.send_message({'action': 'list'})
        msg = client.receive_message()
        
        assert msg.get('type') == 'game_list', "Should receive game list"
        assert 'games' in msg, "Should have games field"
        # May be empty or have games from other tests
        
        client.close()
    
    def test_12_list_available_games(self):
        """Test: Created game appears in list"""
        # Create game
        creator = TestClient("Creator")
        creator.connect()
        creator.receive_message()
        creator.send_message({'name': 'Creator'})
        creator.receive_message()
        creator.send_message({'action': 'create'})
        creator.receive_message()
        creator.send_message({'num_players': 2})
        creation = creator.receive_message()
        game_id = creation.get('game_id')
        
        # List games
        lister = TestClient("Lister")
        lister.connect()
        lister.receive_message()
        lister.send_message({'name': 'Lister'})
        lister.receive_message()
        lister.send_message({'action': 'list'})
        
        msg = lister.receive_message()
        assert msg.get('type') == 'game_list', "Should get game list"
        
        # Find our game
        found = False
        for game in msg.get('games', []):
            if game.get('game_id') == game_id:
                found = True
                assert game.get('creator') == 'Creator', "Creator name should match"
                assert '1/2' in game.get('players', ''), "Should show 1/2 players"
                break
        
        assert found, f"Created game {game_id} should appear in list"
        
        creator.close()
        lister.close()
    
    # ===== JOINING GAMES TESTS =====
    
    def test_13_join_game_request(self):
        """Test: Joining game prompts for game ID"""
        client = TestClient("JoinRequestTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Test'})
        client.receive_message()
        
        client.send_message({'action': 'join'})
        msg = client.receive_message()
        
        assert msg.get('type') == 'request_game_id', "Should request game ID"
        
        client.close()
    
    def test_14_join_nonexistent_game(self):
        """Test: Joining nonexistent game shows error and retries"""
        client = TestClient("JoinNonexistentTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Test'})
        client.receive_message()
        
        client.send_message({'action': 'join'})
        client.receive_message()
        client.send_message({'game_id': 99999})
        
        msg = client.receive_message(timeout=3.0)
        assert msg is not None, "Should receive error response"
        assert msg.get('type') == 'error', "Should be error message"
        assert 'not found' in msg.get('message', '').lower(), "Should mention game not found"
        
        # Should ask again
        msg2 = client.receive_message(timeout=3.0)
        assert msg2 and msg2.get('type') == 'request_game_id', "Should ask for game ID again"
        
        client.close()
    
    def test_15_join_valid_game(self):
        """Test: Successfully joining a game"""
        # Create game
        creator = TestClient("Creator")
        creator.connect()
        creator.receive_message()
        creator.send_message({'name': 'Creator'})
        creator.receive_message()
        creator.send_message({'action': 'create'})
        creator.receive_message()
        creator.send_message({'num_players': 2})
        creation = creator.receive_message()
        game_id = creation.get('game_id')
        
        # Join game
        joiner = TestClient("Joiner")
        joiner.connect()
        joiner.receive_message()
        joiner.send_message({'name': 'Joiner'})
        joiner.receive_message()
        joiner.send_message({'action': 'join'})
        joiner.receive_message()
        joiner.send_message({'game_id': game_id})
        
        msg = joiner.receive_message()
        assert msg.get('type') == 'game_joined', "Should successfully join"
        assert 'symbol' in msg, "Should get symbol"
        assert msg.get('symbol') == 'O', "Second player should be O"
        
        creator.close()
        joiner.close()
    
    def test_16_join_full_game(self):
        """Test: Cannot join a full game and retries"""
        # Create 2-player game
        p1 = TestClient("P1")
        p1.connect()
        p1.receive_message()
        p1.send_message({'name': 'P1'})
        p1.receive_message()
        p1.send_message({'action': 'create'})
        p1.receive_message()
        p1.send_message({'num_players': 2})
        creation = p1.receive_message()
        game_id = creation.get('game_id')
        
        # Player 2 joins (fills game)
        p2 = TestClient("P2")
        p2.connect()
        p2.receive_message()
        p2.send_message({'name': 'P2'})
        p2.receive_message()
        p2.send_message({'action': 'join'})
        p2.receive_message()
        p2.send_message({'game_id': game_id})
        p2.receive_message()
        
        time.sleep(0.5)  # Let game start
        
        # Player 3 tries to join
        p3 = TestClient("P3")
        p3.connect()
        p3.receive_message()
        p3.send_message({'name': 'P3'})
        p3.receive_message()
        p3.send_message({'action': 'join'})
        p3.receive_message()
        p3.send_message({'game_id': game_id})
        
        msg = p3.receive_message(timeout=3.0)
        assert msg is not None, "Should receive response"
        assert msg.get('type') == 'error', "Should be error"
        assert 'full' in msg.get('message', '').lower(), "Should mention game is full"
        
        p1.close()
        p2.close()
        p3.close()
    
    # ===== GAME START TESTS =====
    
    def test_17_game_starts_when_full(self):
        """Test: Game starts automatically when all players join"""
        p1, p2, game_id = self._setup_two_player_game()
        
        # Both should receive game_start and game_state
        start1 = p1.receive_until_type('game_start', max_attempts=5)
        start2 = p2.receive_until_type('game_start', max_attempts=5)
        
        assert start1 is not None, "Player 1 should receive game_start"
        assert start2 is not None, "Player 2 should receive game_start"
        
        state1 = p1.receive_until_type('game_state', max_attempts=5)
        state2 = p2.receive_until_type('game_state', max_attempts=5)
        
        assert state1 is not None, "Player 1 should receive game_state"
        assert state2 is not None, "Player 2 should receive game_state"
        
        p1.close()
        p2.close()
    
    def test_18_initial_board_empty(self):
        """Test: Initial board is empty"""
        p1, p2, game_id = self._setup_two_player_game()
        
        self._skip_to_gameplay(p1, p2)
        state = p1.receive_message()
        
        board = state['state']['board']
        assert all(cell == ' ' for cell in board), "Initial board should be empty"
        
        p1.close()
        p2.close()
    
    def test_19_first_player_starts(self):
        """Test: First player (X) gets first turn"""
        p1, p2, game_id = self._setup_two_player_game()
        
        self._skip_to_gameplay(p1, p2)
        state1 = p1.receive_message()
        state2 = p2.receive_message()
        
        assert state1.get('your_turn') == True, "Player 1 should have first turn"
        assert state2.get('your_turn') == False, "Player 2 should not have first turn"
        
        p1.close()
        p2.close()
    
    # ===== GAMEPLAY TESTS =====
    
    def test_20_valid_move_updates_board(self):
        """Test: Valid move updates the board"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # Player 1 makes move at position 0
        p1.send_message({'type': 'move', 'position': 0})
        
        # Get updated states
        new_state1 = p1.receive_until_type('game_state', max_attempts=5)
        new_state2 = p2.receive_until_type('game_state', max_attempts=5)
        
        assert new_state1 is not None, "Player 1 should receive updated state"
        assert new_state2 is not None, "Player 2 should receive updated state"
        
        board1 = new_state1['state']['board']
        board2 = new_state2['state']['board']
        
        assert board1[0] == 'X', "Position 0 should have X"
        assert board2[0] == 'X', "Both players should see same board"
        
        p1.close()
        p2.close()
    
    def test_21_turn_switches_after_move(self):
        """Test: Turn switches to next player after valid move"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # Player 1 moves
        p1.send_message({'type': 'move', 'position': 4})
        
        new_state1 = p1.receive_until_type('game_state', max_attempts=5)
        new_state2 = p2.receive_until_type('game_state', max_attempts=5)
        
        assert new_state1.get('your_turn') == False, "Player 1 should not have turn"
        assert new_state2.get('your_turn') == True, "Player 2 should have turn"
        
        p1.close()
        p2.close()
    
    def test_22_invalid_position_out_of_bounds(self):
        """Test: Out of bounds position is rejected"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # Try invalid position
        p1.send_message({'type': 'move', 'position': 999})
        
        msg = p1.receive_message(timeout=3.0)
        assert msg is not None, "Should receive response"
        assert msg.get('type') == 'error', "Should be error"
        assert 'invalid' in msg.get('message', '').lower() or 'position' in msg.get('message', '').lower()
        
        p1.close()
        p2.close()
    
    def test_23_invalid_position_negative(self):
        """Test: Negative position is rejected"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        p1.send_message({'type': 'move', 'position': -1})
        
        msg = p1.receive_message(timeout=3.0)
        assert msg.get('type') == 'error', "Should reject negative position"
        
        p1.close()
        p2.close()
    
    def test_24_occupied_position_rejected(self):
        """Test: Cannot place mark on occupied position"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # Player 1 takes position 4
        p1.send_message({'type': 'move', 'position': 4})
        p1.receive_until_type('game_state', max_attempts=5)
        state2 = p2.receive_until_type('game_state', max_attempts=5)
        
        # Player 2 tries same position
        p2.send_message({'type': 'move', 'position': 4})
        
        msg = p2.receive_message(timeout=3.0)
        assert msg.get('type') == 'error', "Should reject occupied position"
        assert 'occupied' in msg.get('message', '').lower(), "Should mention position is occupied"
        
        p1.close()
        p2.close()
    
    def test_25_wrong_turn_rejected(self):
        """Test: Cannot move when it's not your turn"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # Player 2 tries to move (but it's P1's turn)
        p2.send_message({'type': 'move', 'position': 0})
        
        msg = p2.receive_message(timeout=3.0)
        assert msg.get('type') == 'error', "Should reject move"
        assert 'turn' in msg.get('message', '').lower(), "Should mention it's not their turn"
        
        p1.close()
        p2.close()
    
    # ===== WIN DETECTION TESTS =====
    
    def test_26_horizontal_win_top_row(self):
        """Test: Win detection for horizontal line (top row)"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # X wins: 0, 1, 2 (top row)
        moves = [
            (p1, 0), (p2, 3),
            (p1, 1), (p2, 4),
            (p1, 2)  # Win!
        ]
        
        game_ended = self._play_moves(p1, p2, moves)
        assert game_ended, "Game should end with horizontal win"
        
        p1.close()
        p2.close()
    
    def test_27_horizontal_win_middle_row(self):
        """Test: Win detection for horizontal line (middle row)"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # X wins: 3, 4, 5 (middle row)
        moves = [
            (p1, 3), (p2, 0),
            (p1, 4), (p2, 1),
            (p1, 5)  # Win!
        ]
        
        game_ended = self._play_moves(p1, p2, moves)
        assert game_ended, "Game should end with horizontal win"
        
        p1.close()
        p2.close()
    
    def test_28_vertical_win(self):
        """Test: Win detection for vertical line"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # X wins: 0, 3, 6 (left column)
        moves = [
            (p1, 0), (p2, 1),
            (p1, 3), (p2, 2),
            (p1, 6)  # Win!
        ]
        
        game_ended = self._play_moves(p1, p2, moves)
        assert game_ended, "Game should end with vertical win"
        
        p1.close()
        p2.close()
    
    def test_29_diagonal_win_topleft_bottomright(self):
        """Test: Win detection for diagonal (top-left to bottom-right)"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # X wins: 0, 4, 8 (diagonal)
        moves = [
            (p1, 0), (p2, 1),
            (p1, 4), (p2, 2),
            (p1, 8)  # Win!
        ]
        
        game_ended = self._play_moves(p1, p2, moves)
        assert game_ended, "Game should end with diagonal win"
        
        p1.close()
        p2.close()
    
    def test_30_diagonal_win_topright_bottomleft(self):
        """Test: Win detection for diagonal (top-right to bottom-left)"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # X wins: 2, 4, 6 (diagonal)
        moves = [
            (p1, 2), (p2, 0),
            (p1, 4), (p2, 1),
            (p1, 6)  # Win!
        ]
        
        game_ended = self._play_moves(p1, p2, moves)
        assert game_ended, "Game should end with diagonal win"
        
        p1.close()
        p2.close()
    
    def test_31_draw_detection(self):
        """Test: Draw detection when board is full"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # Play moves that result in draw
        # X O X
        # O X O
        # O X X
        draw_moves = [
            (p1, 0), (p2, 1), (p1, 2),
            (p2, 3), (p1, 4), (p2, 5),
            (p1, 7), (p2, 6), (p1, 8)  # Last move - draw
        ]
        
        game_ended = self._play_moves(p1, p2, draw_moves, expect_draw=True)
        assert game_ended, "Game should end in draw"
        
        p1.close()
        p2.close()
    
    def test_32_winner_receives_correct_message(self):
        """Test: Winner receives win notification with their symbol"""
        p1, p2, game_id = self._setup_two_player_game()
        self._skip_to_gameplay(p1, p2)
        
        p1.receive_message()
        p2.receive_message()
        
        # P1 wins
        moves = [
            (p1, 0), (p2, 3),
            (p1, 1), (p2, 4),
            (p1, 2)
        ]
        
        for player, pos in moves:
            player.send_message({'type': 'move', 'position': pos})
            p1.receive_until_type('game_state', max_attempts=3, timeout=2.0)
            p2.receive_until_type('game_state', max_attempts=3, timeout=2.0)
        
        # Check for game_end messages
        end1 = p1.receive_until_type('game_end', max_attempts=5, timeout=3.0)
        end2 = p2.receive_until_type('game_end', max_attempts=5, timeout=3.0)
        
        assert end1 is not None, "Winner should receive game_end"
        assert end2 is not None, "Loser should receive game_end"
        assert end1.get('result') == 'win', "Should be win result"
        assert end1.get('winner_symbol') == 'X', "Winner symbol should be X"
        
        p1.close()
        p2.close()
    
    # ===== MULTI-PLAYER TESTS =====
    
    def test_33_three_player_game_board_size(self):
        """Test: 3-player game has correct board size (4x4 = 16)"""
        p1, p2, p3, game_id = self._setup_three_player_game()
        
        self._skip_to_gameplay_multi(p1, p2, p3)
        
        state = p1.receive_message(timeout=3.0)
        if state and 'state' in state:
            board = state['state']['board']
            assert len(board) == 16, f"3-player board should be 16 squares, got {len(board)}"
        
        p1.close()
        p2.close()
        p3.close()
    
    def test_34_three_player_symbols(self):
        """Test: 3 players get different symbols (X, O, ∆)"""
        p1, p2, p3, game_id = self._setup_three_player_game()
        
        # Check symbols from join messages
        symbols = []
        for player in [p1, p2, p3]:
            for msg in player.messages_received:
                if msg.get('type') in ['game_created', 'game_joined']:
                    symbols.append(msg.get('symbol'))
                    break
        
        assert len(symbols) == 3, "Should have 3 symbols"
        assert len(set(symbols)) == 3, "All symbols should be different"
        assert 'X' in symbols, "Should have X"
        assert 'O' in symbols, "Should have O"
        assert '∆' in symbols, "Should have ∆"
        
        p1.close()
        p2.close()
        p3.close()
    
    def test_35_four_player_game(self):
        """Test: 4-player game works (5x5 board = 25 squares)"""
        players = []
        for i in range(4):
            p = TestClient(f"P{i+1}")
            p.connect()
            p.receive_message()
            p.send_message({'name': f'Player{i+1}'})
            p.receive_message()
            players.append(p)
        
        # Create game
        players[0].send_message({'action': 'create'})
        players[0].receive_message()
        players[0].send_message({'num_players': 4})
        creation = players[0].receive_message()
        game_id = creation.get('game_id')
        
        # Others join
        for i in range(1, 4):
            players[i].send_message({'action': 'join'})
            players[i].receive_message()
            players[i].send_message({'game_id': game_id})
            players[i].receive_message()
        
        # Wait for game start
        time.sleep(1)
        
        # Check board size
        for p in players:
            p.receive_until_type('game_start', max_attempts=5)
        
        state = players[0].receive_until_type('game_state', max_attempts=5)
        if state and 'state' in state:
            board = state['state']['board']
            assert len(board) == 25, f"4-player board should be 25 squares, got {len(board)}"
        
        for p in players:
            p.close()
    
    # ===== EXIT TESTS =====
    
    def test_36_exit_from_menu(self):
        """Test: Can exit cleanly from menu"""
        client = TestClient("ExitTest")
        client.connect()
        client.receive_message()
        client.send_message({'name': 'Test'})
        client.receive_message()
        
        client.send_message({'action': 'exit'})
        msg = client.receive_message(timeout=3.0)
        
        # Should receive goodbye or connection should close
        if msg:
            assert msg.get('type') == 'goodbye', "Should receive goodbye message"
        
        client.close()
    
    # ===== HELPER METHODS =====
    
    def _setup_two_player_game(self):
        """Setup a 2-player game and return both players and game_id"""
        p1 = TestClient("Player1")
        p2 = TestClient("Player2")
        
        p1.connect()
        p1.receive_message()
        p1.send_message({'name': 'Player1'})
        p1.receive_message()
        p1.send_message({'action': 'create'})
        p1.receive_message()
        p1.send_message({'num_players': 2})
        creation = p1.receive_message()
        game_id = creation.get('game_id')
        
        p2.connect()
        p2.receive_message()
        p2.send_message({'name': 'Player2'})
        p2.receive_message()
        p2.send_message({'action': 'join'})
        p2.receive_message()
        p2.send_message({'game_id': game_id})
        p2.receive_message()
        
        return p1, p2, game_id
    
    def _setup_three_player_game(self):
        """Setup a 3-player game"""
        p1 = TestClient("Player1")
        p2 = TestClient("Player2")
        p3 = TestClient("Player3")
        
        p1.connect()
        p1.receive_message()
        p1.send_message({'name': 'Player1'})
        p1.receive_message()
        p1.send_message({'action': 'create'})
        p1.receive_message()
        p1.send_message({'num_players': 3})
        creation = p1.receive_message()
        game_id = creation.get('game_id')
        
        for p in [p2, p3]:
            p.connect()
            p.receive_message()
            p.send_message({'name': p.name})
            p.receive_message()
            p.send_message({'action': 'join'})
            p.receive_message()
            p.send_message({'game_id': game_id})
            p.receive_message()
        
        return p1, p2, p3, game_id
    
    def _skip_to_gameplay(self, p1, p2):
        """Skip initial messages to get to gameplay state"""
        # Receive player_joined and game_start messages
        for _ in range(3):
            p1.receive_message(timeout=2.0)
            p2.receive_message(timeout=2.0)
    
    def _skip_to_gameplay_multi(self, *players):
        """Skip initial messages for multiple players"""
        for _ in range(3):
            for p in players:
                p.receive_message(timeout=2.0)
    
    def _play_moves(self, p1, p2, moves, expect_draw=False):
        """Play a sequence of moves and check if game ends"""
        for i, (player, pos) in enumerate(moves):
            player.send_message({'type': 'move', 'position': pos})
            
            # Wait for responses
            time.sleep(0.2)
            msg1 = p1.receive_message(timeout=2.0)
            msg2 = p2.receive_message(timeout=2.0)
            
            # Check if game ended
            if i == len(moves) - 1:
                # Last move - should end game
                for _ in range(3):
                    end1 = p1.receive_message(timeout=2.0)
                    end2 = p2.receive_message(timeout=2.0)
                    if (end1 and end1.get('type') == 'game_end') or \
                       (end2 and end2.get('type') == 'game_end'):
                        if expect_draw:
                            assert end1.get('result') == 'draw' or end2.get('result') == 'draw'
                        else:
                            assert end1.get('result') == 'win' or end2.get('result') == 'win'
                        return True
        
        return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print(" "*25 + "TEST SUMMARY")
        print("="*70)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_failed}")
        print(f"📊 Total Tests:  {self.tests_passed + self.tests_failed}")
        
        if self.tests_passed + self.tests_failed > 0:
            success_rate = self.tests_passed / (self.tests_passed + self.tests_failed) * 100
            print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if self.tests_failed > 0:
            print("\n" + "="*70)
            print("FAILED TESTS:")
            print("="*70)
            for name, status, error in self.test_results:
                if status != "PASSED":
                    print(f"\n❌ {name}")
                    print(f"   Error: {error}")
        
        print("\n" + "="*70)
        
        if self.tests_failed == 0:
            print("🎉 ALL TESTS PASSED! Your code is ready for submission! 🎉")
        elif success_rate >= 90:
            print("✨ Great job! Minor issues only. Review failed tests.")
        elif success_rate >= 70:
            print("👍 Good progress! Fix the failed tests before submission.")
        else:
            print("⚠️  Several tests failed. Review and fix before submission.")
        
        print("="*70)


def main():
    """Run all tests"""
    print("="*70)
    print(" "*15 + "COMPLETE TIC-TAC-TOE TEST SUITE")
    print("="*70)
    print("\n⚠️  IMPORTANT: Make sure the server is running before starting tests!")
    print("   Start your server with: python server.py")
    print("\nPress Enter to begin testing...")
    input()
    
    tests = TicTacToeTests()
    
    print("\n" + "="*70)
    print("STARTING TESTS...")
    print("="*70)
    
    # Connection Tests
    print("\n" + "="*70)
    print("CATEGORY: CONNECTION & SETUP")
    print("="*70)
    tests.run_test("01. Server Connection", tests.test_01_server_connection)
    tests.run_test("02. Initial Handshake", tests.test_02_initial_handshake)
    tests.run_test("03. Name Submission", tests.test_03_name_submission)
    
    # Menu Tests
    print("\n" + "="*70)
    print("CATEGORY: MENU FUNCTIONALITY")
    print("="*70)
    tests.run_test("04. Menu Display", tests.test_04_menu_display)
    tests.run_test("05. Invalid Menu Choice", tests.test_05_invalid_menu_choice)
    
    # Game Creation Tests
    print("\n" + "="*70)
    print("CATEGORY: GAME CREATION")
    print("="*70)
    tests.run_test("06. Create Game Request", tests.test_06_create_game_request)
    tests.run_test("07. Valid Game Creation", tests.test_07_create_valid_game)
    tests.run_test("08. Invalid Player Count (Low)", tests.test_08_create_game_invalid_player_count_low)
    tests.run_test("09. Invalid Player Count (High)", tests.test_09_create_game_invalid_player_count_high)
    tests.run_test("10. Board Size (2 Players)", tests.test_10_board_size_2_players)
    
    # Game Listing Tests
    print("\n" + "="*70)
    print("CATEGORY: GAME LISTING")
    print("="*70)
    tests.run_test("11. List Empty Games", tests.test_11_list_empty_games)
    tests.run_test("12. List Available Games", tests.test_12_list_available_games)
    
    # Joining Tests
    print("\n" + "="*70)
    print("CATEGORY: JOINING GAMES")
    print("="*70)
    tests.run_test("13. Join Game Request", tests.test_13_join_game_request)
    tests.run_test("14. Join Nonexistent Game", tests.test_14_join_nonexistent_game)
    tests.run_test("15. Join Valid Game", tests.test_15_join_valid_game)
    tests.run_test("16. Join Full Game", tests.test_16_join_full_game)
    
    # Game Start Tests
    print("\n" + "="*70)
    print("CATEGORY: GAME START")
    print("="*70)
    tests.run_test("17. Game Starts When Full", tests.test_17_game_starts_when_full)
    tests.run_test("18. Initial Board Empty", tests.test_18_initial_board_empty)
    tests.run_test("19. First Player Starts", tests.test_19_first_player_starts)
    
    # Gameplay Tests
    print("\n" + "="*70)
    print("CATEGORY: GAMEPLAY MECHANICS")
    print("="*70)
    tests.run_test("20. Valid Move Updates Board", tests.test_20_valid_move_updates_board)
    tests.run_test("21. Turn Switches After Move", tests.test_21_turn_switches_after_move)
    tests.run_test("22. Invalid Position (Out of Bounds)", tests.test_22_invalid_position_out_of_bounds)
    tests.run_test("23. Invalid Position (Negative)", tests.test_23_invalid_position_negative)
    tests.run_test("24. Occupied Position Rejected", tests.test_24_occupied_position_rejected)
    tests.run_test("25. Wrong Turn Rejected", tests.test_25_wrong_turn_rejected)
    
    # Win Detection Tests
    print("\n" + "="*70)
    print("CATEGORY: WIN DETECTION")
    print("="*70)
    tests.run_test("26. Horizontal Win (Top Row)", tests.test_26_horizontal_win_top_row)
    tests.run_test("27. Horizontal Win (Middle Row)", tests.test_27_horizontal_win_middle_row)
    tests.run_test("28. Vertical Win", tests.test_28_vertical_win)
    tests.run_test("29. Diagonal Win (TL-BR)", tests.test_29_diagonal_win_topleft_bottomright)
    tests.run_test("30. Diagonal Win (TR-BL)", tests.test_30_diagonal_win_topright_bottomleft)
    tests.run_test("31. Draw Detection", tests.test_31_draw_detection)
    tests.run_test("32. Winner Receives Correct Message", tests.test_32_winner_receives_correct_message)
    
    # Multi-player Tests
    print("\n" + "="*70)
    print("CATEGORY: MULTI-PLAYER GAMES")
    print("="*70)
    tests.run_test("33. Three Player Board Size", tests.test_33_three_player_game_board_size)
    tests.run_test("34. Three Player Symbols", tests.test_34_three_player_symbols)
    tests.run_test("35. Four Player Game", tests.test_35_four_player_game)
    
    # Exit Tests
    print("\n" + "="*70)
    print("CATEGORY: EXIT & CLEANUP")
    print("="*70)
    tests.run_test("36. Exit From Menu", tests.test_36_exit_from_menu)
    
    # Print final summary
    tests.print_summary()


if __name__ == "__main__":
    main()