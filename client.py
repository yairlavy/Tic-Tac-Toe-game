# client.py
import socket
import threading
from protocol import send, recv_line

current_board = []
my_symbol = None
game_started = False


# ---------------------------------------------------------
#               BEAUTIFUL SCALABLE BOARD
# ---------------------------------------------------------
def print_board():
    if not current_board:
        print("No board available yet.")
        return

    size = len(current_board)

    # Dynamic column header
    print("\n      " + "   ".join(str(i) for i in range(size)))

    # Horizontal line function
    def horiz_line():
        print("    " + "+".join(["-----"] * size))

    # Print top border
    horiz_line()

    for i, row in enumerate(current_board):
        # Row content
        cells = " | ".join(f"{cell:^3}" for cell in row)  # centered cells
        print(f"  {i} | {cells} |")
        horiz_line()

    print()  # spacing


# ---------------------------------------------------------
#                       MENU
# ---------------------------------------------------------
def print_menu():
    print("\n================ GAME MENU ================")
    print("1. List available games")
    print("2. Create a new game")
    print("3. Join a game")
    print("4. Show current board")
    print("5. Make a move")
    print("6. Quit")
    print("===========================================")


def parse_board_lines(lines):
    board = []
    for line in lines:
        row = [c for c in line.split("|")]
        row = [c.strip() for c in row]
        board.append(row)
    return board


# ---------------------------------------------------------
#              SERVER LISTENING THREAD
# ---------------------------------------------------------
def listen_to_server(conn):
    global current_board, my_symbol, game_started

    buffer = []
    reading_board = False

    while True:
        msg = recv_line(conn)
        if msg is None:
            print("\n[SERVER DISCONNECTED]")
            break

        # Capture board lines
        if "|" in msg and not msg.startswith("["):
            reading_board = True
            buffer.append(msg)
            continue

        # Board is finished
        if reading_board:
            current_board = parse_board_lines(buffer)
            buffer = []
            reading_board = False
            print_board()
            continue

        # -------------------------------------------------
        #           INTERPRETED SERVER RESPONSES
        # -------------------------------------------------

        if msg.startswith("WELCOME"):
            print("[Connected to server]")

        elif msg.startswith("GAME_CREATED"):
            parts = msg.split()
            my_symbol = parts[-1]
            print(f"\n[Game created successfully]")
            print(f"[Your symbol]: {my_symbol}")

        elif msg.startswith("JOIN_OK"):
            parts = msg.split()
            my_symbol = parts[-1]
            print(f"\n[Joined game successfully]")
            print(f"[Your symbol]: {my_symbol}")

        elif msg.startswith("GAME_START"):
            game_started = True
            print("\n[The game has started! Waiting for board...]")

        elif msg.startswith("GAME_OVER"):
            print("\n============== GAME OVER ==============")
            print(msg)
            print("=======================================")

        elif msg.startswith("INVALID_MOVE"):
            print("\n[Invalid move — Choose another position]")

        elif msg.startswith("ERROR"):
            print("\n[SERVER ERROR]:", msg)

        elif msg.startswith("NO_GAMES"):
            print("\n[No available games]")

        elif msg.startswith("GAME"):
            print("[Available game]:", msg)

        elif msg.startswith("END_LIST"):
            print("[End of list]")

        else:
            print("[SERVER]:", msg)


# ---------------------------------------------------------
#                     MAIN LOOP
# ---------------------------------------------------------
def main():
    global current_board, game_started

    # Connect
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(("127.0.0.1", 5000))
    print("Connected to server.")

    # Background listener
    threading.Thread(target=listen_to_server, args=(conn,), daemon=True).start()

    # Main menu loop
    while True:
        print_menu()
        choice = input("Choose (1-6): ").strip()

        if choice == "1":
            send(conn, "LIST")

        elif choice == "2":
            p = input("How many players? (2, 3, 4...): ").strip()
            send(conn, f"CREATE {p}")

        elif choice == "3":
            gid = input("Enter game ID: ").strip()
            send(conn, f"JOIN {gid}")

        elif choice == "4":
            print_board()

        elif choice == "5":
            if not game_started:
                print("\n[Game not started yet!]")
                continue

            print("\nEnter your move:")
            r = input("Row: ").strip()
            c = input("Col: ").strip()
            send(conn, f"MOVE {r} {c}")

        elif choice == "6":
            print("Goodbye!")
            send(conn, "QUIT")
            break

        else:
            print("Invalid option.")

    conn.close()


if __name__ == "__main__":
    main()
