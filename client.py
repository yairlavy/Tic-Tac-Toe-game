"""
Tic-Tac-Toe Game Client 
Client application for connecting to the game server
"""

import socket
import json
import threading
import time

# Client Configuration
HOST = '127.0.0.1'
PORT = 5000
FORMAT = 'utf-8'
ADDR = (HOST, PORT)
MESSAGE_DELIMITER = '\n<END>\n'


class TicTacToeClient:
    """Client class for Tic-Tac-Toe game"""
    
    def __init__(self):
        self.client_socket = None
        self.connected = False
        self.player_name = ""
        self.in_game = False
        self.my_symbol = ""
        self.buffer = ""  # Buffer for incomplete messages
    
    def connect(self):
        """Connect to the server"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(ADDR)
            self.connected = True
            print(f"[CONNECTED] Connected to server at {HOST}:{PORT}")
            return True
        except Exception as e:
            print(f"[ERROR] Could not connect to server: {e}")
            return False
    
    def send_message(self, message):
        """Send a message to the server"""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            message_with_delimiter = message + MESSAGE_DELIMITER
            self.client_socket.send(message_with_delimiter.encode(FORMAT))
            return True
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")
            return False
    
    def receive_message(self):
        """Receive a message from the server"""
        try:
            data = self.client_socket.recv(4096).decode(FORMAT)
            if data:
                self.buffer += data
                
                # Check if we have a complete message
                if MESSAGE_DELIMITER in self.buffer:
                    parts = self.buffer.split(MESSAGE_DELIMITER, 1)
                    message = parts[0]
                    self.buffer = parts[1] if len(parts) > 1 else ""
                    
                    try:
                        return json.loads(message)
                    except:
                        return {'type': 'text', 'message': message}
                else:
                    # No complete message yet, try to receive more
                    return self.receive_message()
            return None
        except Exception as e:
            return None
    
    def display_board(self, board_str):
        """Display the game board"""
        print("\n" + "="*50)
        print(board_str)
        print("="*50)
    
    def display_game_info(self, state):
        """Display game information"""
        print(f"\n[GAME INFO]")
        print(f"Players: {', '.join([f'{name} ({symbol})' for name, symbol in state['players']])}")
        if state['game_over']:
            print("[STATUS] Game Over!")
        elif not state['game_started']:
            print("[STATUS] Waiting for players...")
        else:
            current_player = state['players'][state['current_player']]
            print(f"[CURRENT TURN] {current_player[0]} ({current_player[1]})")
    
    def handle_menu(self):
        """Handle the main menu"""
        while self.connected and not self.in_game:
            response = self.receive_message()
            
            if response is None:
                print("[ERROR] Lost connection to server")
                self.connected = False
                break
            
            msg_type = response.get('type', '') if isinstance(response, dict) else ''
            
            if msg_type == 'request_name':
                # Server asking for name
                self.player_name = input("Enter your name: ").strip()
                if not self.player_name:
                    self.player_name = "Player"
                self.send_message({'name': self.player_name})
                
            elif msg_type == 'menu':
                # Display menu and get choice
                print("\n" + "="*50)
                print(response['message'])
                print("="*50)
                choice = input("Your choice: ").strip()
                
                if choice == '1':
                    self.send_message({'action': 'create'})
                    self.handle_create_game()
                elif choice == '2':
                    self.send_message({'action': 'list'})
                elif choice == '3':
                    self.send_message({'action': 'join'})
                    self.handle_join_game()
                elif choice == '4':
                    self.send_message({'action': 'exit'})
                    self.connected = False
                    break
                else:
                    print("[ERROR] Invalid choice")
                    self.send_message({'action': 'menu'})
            
            elif msg_type == 'game_list':
                # Display available games
                games = response['games']
                print("\n" + "="*50)
                print("Available Games:")
                if not games:
                    print("No games available. Create a new one!")
                else:
                    print(f"{'ID':<6} {'Creator':<15} {'Players':<10} {'Board':<10}")
                    print("-" * 50)
                    for game in games:
                        print(f"{game['game_id']:<6} {game['creator']:<15} {game['players']:<10} {game['board_size']:<10}")
                print("="*50)
            
            elif msg_type == 'error':
                print(f"[ERROR] {response['message']}")
            
            elif msg_type == 'goodbye':
                print(response['message'])
                self.connected = False
                break
            
            elif msg_type == 'text':
                # Handle plain text messages
                print(response.get('message', ''))
    
    def handle_create_game(self):
        """Handle game creation"""
        # Loop until valid number of players is entered
        while True:
            response = self.receive_message()
            
            if response and response.get('type') == 'request_players':
                print(response['message'])
                num_players = input("Number of players: ").strip()
                
                try:
                    num_players = int(num_players)
                    if num_players < 2 or num_players > 8:
                        print("[ERROR] Number must be between 2 and 8")
                        self.send_message({'num_players': -1})  # Send invalid to get asked again
                        continue  # Ask again
                except:
                    print("[ERROR] Invalid number")
                    self.send_message({'num_players': -1})  # Send invalid to get asked again
                    continue  # Ask again
                
                self.send_message({'num_players': num_players})
                break  # Valid input, exit loop
        
        # Wait for game creation confirmation
        response = self.receive_message()
        if response and response.get('type') == 'game_created':
            self.my_symbol = response['symbol']
            print(f"\n[SUCCESS] {response['message']}")
            print(f"Your symbol: {self.my_symbol}")
            self.in_game = True
            self.handle_gameplay()
    
    def handle_join_game(self):
        """Handle joining a game"""
        # Loop until valid game is joined
        while True:
            response = self.receive_message()
            
            if response and response.get('type') == 'request_game_id':
                print(response['message'])
                game_id = input("Game ID: ").strip()
                
                try:
                    game_id = int(game_id)
                except:
                    print("[ERROR] Invalid game ID")
                    self.send_message({'game_id': -1})  # Send invalid to get asked again
                    continue  # Ask again
                
                self.send_message({'game_id': game_id})
                
                # Wait for join confirmation or error
                response = self.receive_message()
                if response:
                    if response.get('type') == 'game_joined':
                        self.my_symbol = response['symbol']
                        print(f"\n[SUCCESS] {response['message']}")
                        self.in_game = True
                        self.handle_gameplay()
                        break  # Successfully joined, exit loop
                    elif response.get('type') == 'error':
                        print(f"[ERROR] {response['message']}")
                        # Continue loop to ask again
    
    def handle_gameplay(self):
        """Handle the actual gameplay"""
        print("\n[GAME] Waiting for game to start...")
        
        game_over = False
        
        while self.in_game and not game_over and self.connected:
            response = self.receive_message()
            
            if response is None:
                print("[ERROR] Lost connection during game")
                self.connected = False
                break
            
            # Ensure response is a dictionary
            if not isinstance(response, dict):
                continue
            
            msg_type = response.get('type', '')
            
            if msg_type == 'player_joined':
                print(f"\n[INFO] {response['message']}")
            
            elif msg_type == 'game_start':
                print(f"\n[GAME] {response['message']}")
            
            elif msg_type == 'game_state':
                # Display game state
                state = response['state']
                self.display_board(state['board_str'])
                self.display_game_info(state)
                
                if response.get('your_turn'):
                    print(f"\n[YOUR TURN] You are {self.my_symbol}")
                    
                    # Get player's move - loop until valid move
                    move_made = False
                    while not move_made and self.connected:
                        try:
                            position = input("Enter position (number on board): ").strip()
                            position = int(position)
                            
                            # Send move to server
                            if self.send_message({
                                'type': 'move',
                                'position': position
                            }):
                                # Wait for server response
                                move_response = self.receive_message()
                                
                                if move_response:
                                    if move_response.get('type') == 'error':
                                        # Invalid move, show error and try again
                                        print(f"[ERROR] {move_response['message']}")
                                        print("Please try again.")
                                        # Continue loop to ask for input again
                                        continue
                                    else:
                                        # Valid move accepted, exit input loop
                                        move_made = True
                                        # Process the response (will be handled in next iteration of main loop)
                                        # Put it back for processing
                                        if move_response.get('type') == 'game_state':
                                            state = move_response['state']
                                            self.display_board(state['board_str'])
                                            self.display_game_info(state)
                                            if not state['game_over']:
                                                current_player = state['players'][state['current_player']]
                                                print(f"\n[WAITING] Waiting for {current_player[0]}'s move...")
                                        elif move_response.get('type') == 'game_end':
                                            # Game ended with this move
                                            print("\n" + "="*50)
                                            if move_response['result'] == 'win':
                                                winner_symbol = move_response.get('winner_symbol')
                                                winner_name = move_response['winner']
                                                if winner_symbol == self.my_symbol:
                                                    print("CONGRATULATIONS! YOU WON!")
                                                    print(f"Winner: {winner_name} ({winner_symbol})")
                                                else:
                                                    print(f"YOU LOST!")
                                                    print(f"Winner: {winner_name} ({winner_symbol})")
                                            elif move_response['result'] == 'draw':
                                                print("Game Over! It's a draw!")
                                            print("="*50)
                                            game_over = True
                                            self.in_game = False
                                            self.connected = False
                                            return
                            else:
                                break
                        except ValueError:
                            print("[ERROR] Please enter a valid number")
                            # Continue loop to ask again
                        except KeyboardInterrupt:
                            print("\n[EXITING] Closing connection...")
                            self.connected = False
                            self.in_game = False
                            return
                        except Exception as e:
                            print(f"[ERROR] {e}")
                            break
                else:
                    if state['game_started'] and not state['game_over']:
                        current_player = state['players'][state['current_player']]
                        print(f"\n[WAITING] Waiting for {current_player[0]}'s move...")
            
            elif msg_type == 'error':
                print(f"[ERROR] {response['message']}")
                # After error, continue waiting for next state (don't break)
            
            elif msg_type == 'game_end':
                # Game ended
                print("\n" + "="*50)
                if response['result'] == 'win':
                    winner_symbol = response.get('winner_symbol')
                    winner_name = response['winner']
                    if winner_symbol == self.my_symbol:
                        print("CONGRATULATIONS! YOU WON!")
                        print(f"Winner: {winner_name} ({winner_symbol})")
                    else:
                        print(f"YOU LOST!")
                        print(f"Winner: {winner_name} ({winner_symbol})")
                elif response['result'] == 'draw':
                    print("Game Over! It's a draw!")
                print("="*50)
                
                game_over = True
                self.in_game = False
                self.connected = False
            
            elif msg_type == 'text':
                # Handle any plain text messages
                print(response.get('message', ''))
    
    def start(self):
        """Start the client"""
        if self.connect():
            try:
                self.handle_menu()
            except KeyboardInterrupt:
                print("\n[EXITING] Closing connection...")
            except Exception as e:
                print(f"[ERROR] Unexpected error: {e}")
            finally:
                if self.client_socket:
                    try:
                        self.client_socket.close()
                    except:
                        pass
                print("[DISCONNECTED] Goodbye!")


def main():
    """Main function"""
    print("="*50)
    print("  TIC-TAC-TOE GAME CLIENT")
    print("="*50)
    
    client = TicTacToeClient()
    client.start()


if __name__ == "__main__":
    main()