# client.py
"""
Tic-Tac-Toe game client with interactive menu interface.
Connects to server, displays game board, and handles user input.
"""
import socket
import threading
from protocol import send, recv_line

current_board = []
my_symbol = None
game_started = False

print_lock = threading.Lock()


# ---------------------------------------------------------
#               BEAUTIFUL SCALABLE BOARD
# ---------------------------------------------------------
def print_board():
    """
    Prints the game board in a formatted grid layout.
    Dynamically adjusts to any board size (3x3, 4x4, 5x5, etc.)
    """
    with print_lock:
        if not current_board:
            print("No board available yet.")
            return

        size = len(current_board)

        # Column header with proper spacing
        print("\n      ", end="")
        for i in range(size):
            print(f"{i:^5}", end="")
        print()

        # Top border
        print("    +" + "-----+" * size)

        # Print each row
        for i, row in enumerate(current_board):
            # Row content with centered cells
            print(f"  {i} |", end="")
            for cell in row:
                # Center each cell content in a 5-character space
                print(f"{cell:^5}|", end="")
            print()
            
            # Horizontal separator between rows
            print("    +" + "-----+" * size)

        print()  # spacing


# ---------------------------------------------------------
#                       MENU
# ---------------------------------------------------------
def print_menu():
    """Displays the main game menu with current player symbol."""
    with print_lock:
        print("\n================ GAME MENU ================")
        print(f"Your symbol: {my_symbol if my_symbol else 'None'}")
        print("1. List available games")
        print("2. Create a new game")
        print("3. Join a game")
        print("4. Show current board")
        print("5. Make a move")
        print("6. Quit")
        print("===========================================")


def parse_board_lines(lines):
    """
    Parses board data received from server into 2D list.
    
    Args:
        lines: List of strings containing pipe-separated cell values
        
    Returns:
        2D list representing the game board
    """
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
    """
    Background thread that continuously listens for server messages.
    Handles board updates, game state changes, and notifications.
    
    Args:
        conn: Socket connection to the server
    """
    global current_board, my_symbol, game_started

    buffer = []
    reading_board = False

    while True:
        msg = recv_line(conn)
        if msg is None:
            with print_lock:
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
            print_menu()
            continue

        # -------------------------------------------------
        #           INTERPRETED SERVER RESPONSES
        # -------------------------------------------------

        if msg.startswith("WELCOME"):
            with print_lock:
                print("[Connected to server]")

        elif msg.startswith("GAME_CREATED"):
            parts = msg.split()
            game_id = parts[1]
            my_symbol = parts[-1]
            with print_lock:
                print(f"\n[Game created successfully]")
                print(f"[Game ID]: {game_id}")
                print(f"[Your symbol]: {my_symbol}")

        elif msg.startswith("JOIN_OK"):
            parts = msg.split()
            my_symbol = parts[-1]
            with print_lock:
                print(f"\n[Joined game successfully]")
                print(f"[Your symbol]: {my_symbol}")

        elif msg.startswith("GAME_START"):
            game_started = True
            with print_lock:
                print("\n[The game has started! Waiting for board...]")

        elif msg.startswith("TURN"):
            parts = msg.split()
            turn_symbol = parts[1]
            with print_lock:
                if turn_symbol == my_symbol:
                    print(f"\n>>> YOUR TURN ({my_symbol}) <<<")
                else:
                    print(f"\n[Waiting for player {turn_symbol} to move...]")

        elif msg.startswith("GAME_OVER"):
            with print_lock:
                print("\n============== GAME OVER ==============")
                print(msg)
                print("=======================================")
                game_started = False  # Reset game state

        elif msg.startswith("INVALID_MOVE"):
            with print_lock:
                print("\n[Invalid move — Choose another position]")

        elif msg.startswith("ERROR"):
            with print_lock:
                print("\n[SERVER ERROR]:", msg)

        elif msg.startswith("NO_GAMES"):
            with print_lock:
                print("\n[No available games]")

        elif msg.startswith("GAME"):
            with print_lock:
                print("[Available game]:", msg)

        elif msg.startswith("END_LIST"):
            with print_lock:
                print("[End of list]")

        else:
            with print_lock:
                print("[SERVER]:", msg)


# ---------------------------------------------------------
#                     MAIN LOOP
# ---------------------------------------------------------
def main():
    """
    Main client loop. Connects to server, starts listener thread,
    and processes user menu selections.
    """
    global current_board, game_started

    # Connect to server
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conn.connect(("127.0.0.1", 5000))
        print("Connected to server.")
    except ConnectionRefusedError:
        print("ERROR: Could not connect to server. Is the server running?")
        return

    # Background listener thread
    threading.Thread(target=listen_to_server, args=(conn,), daemon=True).start()

    # Main menu loop
    while True:
        print_menu()
        choice = input("Choose (1-6): ").strip()

        if choice == "1":
            # List all available games
            send(conn, "LIST")

        elif choice == "2":
            # Create a new game
            p = input("How many players? (2, 3, 4...): ").strip()
            send(conn, f"CREATE {p}")

        elif choice == "3":
            # Join an existing game
            gid = input("Enter game ID: ").strip()
            send(conn, f"JOIN {gid}")

        elif choice == "4":
            # Display current board
            print_board()

        elif choice == "5":
            # Make a move
            if not game_started:
                print("\n[Game not started yet!]")
                continue

            print("\nEnter your move:")
            r = input("Row: ").strip()
            c = input("Col: ").strip()
            send(conn, f"MOVE {r} {c}")

        elif choice == "6":
            # Quit game
            print("Goodbye!")
            send(conn, "QUIT")
            break

        else:
            print("Invalid option.")

    conn.close()


if __name__ == "__main__":
    main()