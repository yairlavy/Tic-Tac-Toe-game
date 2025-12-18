# server.py
"""
Multi-client Tic-Tac-Toe game server.
Handles multiple concurrent games, player connections, and game logic coordination.
"""
import socket
import threading
from protocol import send, recv_line
from game_manager import GameManager

manager = GameManager()


def broadcast(game, msg):
    """
    Sends a message to all players in a specific game.
    
    Args:
        game: Game object containing player connections
        msg: Message string to broadcast
    """
    for conn, _ in game.players:
        try:
            send(conn, msg)
        except:
            # Connection might be closed, skip
            pass


def handle_client(conn, addr):
    """
    Handles communication with a single client.
    Processes commands and coordinates game flow.
    
    Args:
        conn: Socket connection to the client
        addr: Client address tuple (ip, port)
    """
    send(conn, "WELCOME")
    current_game = None
    my_symbol = None

    try:
        while True:
            line = recv_line(conn)
            if line is None:
                break

            parts = line.split()
            cmd = parts[0].upper()

            # LIST - Show all available games
            if cmd == "LIST":
                games = manager.list_games()
                if not games:
                    send(conn, "NO_GAMES")
                else:
                    for g in games:
                        send(conn, f"GAME {g.game_id} {len(g.players)}/{g.max_players}")
                send(conn, "END_LIST")

            # CREATE <players> - Create a new game
            elif cmd == "CREATE":
                max_players = int(parts[1])
                current_game = manager.create_game(max_players)
                my_symbol = current_game.add_player(conn)

                send(conn, f"GAME_CREATED {current_game.game_id} SYMBOL {my_symbol}")

            # JOIN <id> - Join an existing game
            elif cmd == "JOIN":
                gid = int(parts[1])
                current_game = manager.get_game(gid)
                if not current_game:
                    send(conn, "ERROR NO_SUCH_GAME")
                    continue

                my_symbol = current_game.add_player(conn)
                if not my_symbol:
                    send(conn, "ERROR GAME_FULL")
                    continue

                send(conn, f"JOIN_OK SYMBOL {my_symbol}")

                # Start game when all players have joined
                if current_game.all_players_joined():
                    broadcast(current_game, "GAME_START")
                    
                    # Send initial empty board
                    for row in current_game.board:
                        broadcast(current_game, " | ".join(row))
                    
                    # Notify players of the first turn
                    broadcast(current_game, f"TURN {current_game.current_symbol()}")

            # MOVE r c - Make a move at position (r, c)
            elif cmd == "MOVE":
                if not current_game:
                    send(conn, "ERROR NOT_IN_GAME")
                    continue

                row = int(parts[1])
                col = int(parts[2])

                # Validate it's the player's turn
                if my_symbol != current_game.current_symbol():
                    send(conn, "ERROR NOT_YOUR_TURN")
                    continue

                # Validate the move
                if not current_game.is_valid_move(row, col):
                    send(conn, "INVALID_MOVE")
                    continue

                # Apply the move
                current_game.apply_move(my_symbol, row, col)

                # Broadcast updated board to all players
                broadcast(current_game, "")
                for row_line in current_game.board:
                    broadcast(current_game, " | ".join(row_line))

                # Check for winner
                if current_game.check_winner(my_symbol):
                    broadcast(current_game, f"GAME_OVER WINNER {my_symbol}")
                    current_game.game_over = True
                    continue

                # Check for draw
                if current_game.is_draw():
                    broadcast(current_game, "GAME_OVER DRAW")
                    current_game.game_over = True
                    continue

                # Move to next player's turn
                current_game.advance_turn()
                broadcast(current_game, f"TURN {current_game.current_symbol()}")

            # QUIT - Disconnect from server
            elif cmd == "QUIT":
                send(conn, "BYE")
                break

    except Exception as e:
        # Log error in production
        print(f"Error handling client {addr}: {e}")

    finally:
        conn.close()
        print("Client disconnected:", addr)
        
        # Handle player disconnection and game cleanup
        if current_game and not current_game.game_over and my_symbol is not None:
            # Remove the disconnected player from the game
            current_game.players = [p for p in current_game.players if p[0] != conn]
            
            # Notify remaining players
            if len(current_game.players) > 0:
                broadcast(current_game, f"GAME_OVER OPPONENT_LEFT {my_symbol}")
                current_game.game_over = True


def main():
    """
    Main server function. Initializes server socket, binds to port,
    and accepts incoming client connections.
    """
    HOST = "0.0.0.0"  # Listen on all network interfaces
    PORT = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow immediate port reuse when server restarts
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Server listening on {HOST}:{PORT}")
    except socket.error as e:
        print(f"Could not bind to port {PORT}. Error: {e}")
        return

    print("Waiting for clients to connect...")

    while True:
        try:
            # Accept new client connection
            conn, addr = server_socket.accept()
            print(f"New client connected: {addr}")
            
            # Start a new thread to handle this client
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True  # Thread will close when main program exits
            thread.start()
            
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            break
        except Exception as e:
            print(f"Error accepting connection: {e}")
            
    server_socket.close()


if __name__ == "__main__":
    main()