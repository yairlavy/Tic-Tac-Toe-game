# server.py
import socket
import threading
from protocol import send, recv_line
from game_manager import GameManager

manager = GameManager()


def broadcast(game, msg):
    for conn, _ in game.players:
        send(conn, msg)


def handle_client(conn, addr):
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

            # LIST
            if cmd == "LIST":
                for g in manager.list_games():
                    send(conn, f"GAME {g.game_id} {len(g.players)}/{g.max_players}")
                send(conn, "END_LIST")

            # CREATE <players>
            elif cmd == "CREATE":
                max_players = int(parts[1])
                current_game = manager.create_game(max_players)
                my_symbol = current_game.add_player(conn)

                send(conn, f"GAME_CREATED {current_game.game_id} SYMBOL {my_symbol}")

            # JOIN <id>
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

                # Start when full
                if current_game.all_players_joined():
                    broadcast(current_game, "GAME_START")
                    for row in current_game.board:
                        broadcast(current_game, " | ".join(row))

            # MOVE r c
            elif cmd == "MOVE":
                if not current_game:
                    send(conn, "ERROR NOT_IN_GAME")
                    continue

                row = int(parts[1])
                col = int(parts[2])

                # Check turn
                if my_symbol != current_game.current_symbol():
                    send(conn, "ERROR NOT_YOUR_TURN")
                    continue

                if not current_game.is_valid_move(row, col):
                    send(conn, "INVALID_MOVE")
                    continue

                current_game.apply_move(my_symbol, row, col)

                # Send updated board
                broadcast(current_game, "")
                for row_line in current_game.board:
                    broadcast(current_game, " | ".join(row_line))

                # Winner?
                if current_game.check_winner(my_symbol):
                    broadcast(current_game, f"GAME_OVER WINNER {my_symbol}")
                    current_game.game_over = True
                    continue

                # Draw?
                if current_game.is_draw():
                    broadcast(current_game, "GAME_OVER DRAW")
                    current_game.game_over = True
                    continue

                # Next turn
                current_game.advance_turn()

                broadcast(current_game, f"TURN {current_game.current_symbol()}")

            # QUIT
            elif cmd == "QUIT":
                send(conn, "BYE")
                break

    except:
        pass

    finally:
        conn.close()
        print("Client disconnected:", addr)
