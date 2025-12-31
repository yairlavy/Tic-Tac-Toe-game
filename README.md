# Tic-Tac-Toe Game - Documentation

## Student Information
**Name:** [Your Full Name]  
**ID:** [Your ID Number]  
**Operating System:** [e.g., Windows 11, Ubuntu 22.04, macOS 14]  
**Python Version:** [e.g., Python 3.10.5]

---

## Project Overview

This project implements a multi-client Tic-Tac-Toe game using Python sockets. The implementation follows the client-server architecture and supports:
- Multiple concurrent games
- 2-8 players per game
- Dynamic board sizes based on player count: (num_players + 1)²
- Real-time game state updates
- Thread-safe game management

---

## Files Description

### 1. `Server.py` - Game Server
**Purpose:** Manages all game logic, client connections, and game states.

#### Key Classes:

**`Game` Class:**
- Manages individual game instances
- Attributes:
  - `game_id`: Unique identifier for the game
  - `num_players`: Number of players (2-8)
  - `board_size`: Calculated as (num_players + 1)²
  - `board`: List representing the game board
  - `players`: List of connected players with their symbols
  - `current_player_idx`: Index of the player whose turn it is
  - `game_started`: Boolean indicating if game has begun
  - `game_over`: Boolean indicating if game has ended
  - `symbols`: List of symbols for players ['X', 'O', '∆', '□', '◇', '★', '♦', '♣']

**Methods:**
- `add_player(conn, addr, name)`: Adds a player to the game
- `make_move(player_idx, position)`: Processes a player's move
- `check_winner(symbol)`: Checks if a player has won (3 in a row)
- `check_draw()`: Checks if the game is a draw
- `get_board_str()`: Returns formatted board string for display
- `get_game_state()`: Returns complete game state as dictionary

#### Key Functions:

**`handle_client(conn, addr)`:**
- Main handler for client connections
- Manages menu navigation
- Handles game creation and joining
- Parameters:
  - `conn`: Socket connection object
  - `addr`: Client address tuple (IP, port)

**`handle_game_client(conn, addr, game, player_idx)`:**
- Manages gameplay for a specific player
- Receives moves and broadcasts game state
- Detects win/draw conditions

**`broadcast_game_state(game)`:**
- Sends current game state to all players in a game
- Updates each player on their turn status

**`start_server()`:**
- Initializes server socket
- Listens for incoming connections
- Creates new thread for each client

#### Global Variables:
- `games`: Dictionary storing all active games {game_id: Game object}
- `game_id_counter`: Counter for assigning unique game IDs
- `games_lock`: Threading lock for thread-safe game access

---

### 2. `Client.py` - Game Client
**Purpose:** Provides user interface for connecting to server and playing games.

#### Key Class:

**`TicTacToeClient` Class:**
- Manages client-side operations

**Attributes:**
- `client_socket`: Socket connection to server
- `connected`: Connection status
- `player_name`: Player's chosen name
- `in_game`: Boolean indicating if player is in an active game
- `my_symbol`: Player's assigned symbol

**Methods:**
- `connect()`: Establishes connection to server
- `send_message(message)`: Sends JSON-encoded messages to server
- `receive_message()`: Receives and decodes messages from server
- `display_board(board_str)`: Displays the game board
- `display_game_info(state)`: Shows current game information
- `handle_menu()`: Manages main menu interactions
- `handle_create_game()`: Handles game creation flow
- `handle_join_game()`: Handles joining existing games
- `handle_gameplay()`: Manages the actual gameplay loop
- `start()`: Main entry point for client

---

## Communication Protocol

The client and server communicate using JSON-formatted messages over TCP sockets.

### Message Types:

#### Server to Client:
1. **`request_name`** - Requests player name
2. **`menu`** - Sends main menu options
3. **`game_list`** - Lists available games
4. **`game_created`** - Confirms game creation
5. **`game_joined`** - Confirms joining a game
6. **`game_start`** - Notifies game is starting
7. **`game_state`** - Updates current game state
8. **`game_end`** - Notifies game ended with result
9. **`player_joined`** - Notifies when a player joins
10. **`error`** - Error message
11. **`goodbye`** - Disconnect message

#### Client to Server:
1. **`{name: "player_name"}`** - Player identification
2. **`{action: "create/list/join/exit"}`** - Menu choice
3. **`{num_players: n}`** - Number of players for new game
4. **`{game_id: id}`** - Game ID to join
5. **`{type: "move", position: n}`** - Player's move

---

## Game Rules

### Standard Game (2 players):
- Board: 3x3 grid (9 squares)
- Players: X and O
- Win condition: 3 in a row (horizontal, vertical, or diagonal)

### Extended Game (3+ players):
- Board: (n+1)² grid where n = number of players
  - 3 players: 4x4 grid (16 squares)
  - 4 players: 5x5 grid (25 squares)
  - etc.
- Players: X, O, ∆, □, ◇, ★, ♦, ♣
- Win condition: Still 3 in a row (not n in a row)

### Gameplay:
1. Players take turns placing their symbol on an empty square
2. First player to get 3 of their symbols in a row wins
3. If the board fills with no winner, the game is a draw
4. Positions are numbered starting from 0

---

## Usage Instructions

### Starting the Server:
```bash
python Server.py
```

The server will:
- Bind to 127.0.0.1:5000
- Display listening status
- Show active connection count
- Log client connections and game events

### Starting a Client:
```bash
python Client.py
```

The client will:
1. Connect to the server
2. Prompt for player name
3. Display main menu with options:
   - **Create new game**: Start a new game and wait for others
   - **List available games**: View games waiting for players
   - **Join game**: Join an existing game by ID
   - **Exit**: Disconnect from server

### Creating a Game:
1. Select option 1 from menu
2. Enter number of players (2-8)
3. Wait for other players to join
4. Game starts automatically when full

### Joining a Game:
1. Select option 2 to list available games
2. Select option 3 to join
3. Enter the game ID from the list
4. Wait for game to fill and start

### Playing:
1. View the current board state
2. When it's your turn, enter the position number (shown on empty squares)
3. Wait for other players' turns
4. Game ends when someone wins or board is full

---

## Technical Implementation Details

### Threading Model:
- Server uses one thread per client connection
- Each game maintains its own lock for thread-safe operations
- Global `games_lock` protects the games dictionary

### Socket Communication:
- Protocol: TCP (SOCK_STREAM)
- Encoding: UTF-8
- Message format: JSON
- Buffer size: 4096 bytes

### Error Handling:
- Connection interruptions handled gracefully
- Invalid moves rejected with error messages
- Full game prevention
- Input validation on server side

### Concurrency Features:
- Multiple games can run simultaneously
- Thread-safe game state management
- Real-time updates to all players

---

## Example Gameplay

### Server Output:
```
[STARTING] Tic-Tac-Toe server is starting...
[LISTENING] Server is listening on 127.0.0.1:5000
[ACTIVE CONNECTIONS] 0
[CLIENT CONNECTED] ('127.0.0.1', 54321)
[CLIENT] ('127.0.0.1', 54321) identified as Alice
[GAME CREATED] Game 0 by Alice
[CLIENT CONNECTED] ('127.0.0.1', 54322)
[CLIENT] ('127.0.0.1', 54322) identified as Bob
[GAME 0] Bob joined
```

### Client Output:
```
==================================================
  TIC-TAC-TOE GAME CLIENT
==================================================
[CONNECTED] Connected to server at 127.0.0.1:5000
Enter your name: Alice

==================================================
Choose an option:
1. Create new game
2. List available games
3. Join game
4. Exit
==================================================
Your choice: 1
Number of players: 2

[SUCCESS] Game 0 created! Waiting for 1 more players...
Your symbol: X

[INFO] Bob joined the game!
[GAME] Game starting!

==================================================
  0   1   2
  ---+---+---
0| 0 | 1 | 2 |
  ---+---+---
1| 3 | 4 | 5 |
  ---+---+---
2| 6 | 7 | 8 |
==================================================

[GAME INFO]
Players: Alice (X), Bob (O)
[CURRENT TURN] Alice (X)

[YOUR TURN] You are X
Enter position (number on board): 4
```

---

## Screenshots

### 1. Server Starting
![Server start screen showing initialization and listening status]

### 2. Client Connection
![Client connecting and entering name]

### 3. Game Creation
![Creating a new game with player count selection]

### 4. Game List
![Viewing available games with details]

### 5. Active Gameplay
![Game board with current state and turn information]

### 6. Game End
![Victory or draw message with final board state]

---

## Testing Recommendations

1. **Single Game Test:**
   - Start server
   - Connect 2 clients
   - Complete a full game

2. **Multiple Games Test:**
   - Start server
   - Create multiple games with different player counts
   - Verify games run independently

3. **Disconnect Test:**
   - Start a game
   - Disconnect a client mid-game
   - Verify server handles gracefully

4. **Edge Cases:**
   - Try invalid positions
   - Attempt moves out of turn
   - Test maximum players (8)
   - Test minimum players (2)

---

## Potential Enhancements

1. **Reconnection Support:** Allow players to reconnect if disconnected
2. **Game History:** Save and display past game results
3. **Spectator Mode:** Allow users to watch ongoing games
4. **Chat Feature:** In-game messaging between players
5. **AI Opponent:** Computer player for single-player mode
6. **GUI Interface:** Graphical user interface using tkinter or pygame
7. **Authentication:** User accounts and login system
8. **Leaderboards:** Track wins/losses across sessions

---

## Known Limitations

1. No persistent storage - games lost if server restarts
2. No reconnection mechanism for disconnected players
3. Fixed localhost address (not configurable without code change)
4. No authentication or security features
5. Limited error recovery for network issues

---

## Conclusion

This implementation successfully meets all assignment requirements:
- ✅ Multi-client socket-based server
- ✅ Concurrent game handling
- ✅ Proper move validation
- ✅ Win/draw detection
- ✅ Client UI for game interaction
- ✅ Real-time game state updates
- ✅ Game creation and joining
- ✅ Graceful disconnection

The code is well-documented, follows Python best practices, and demonstrates understanding of socket programming, threading, and client-server architecture.
