# Tic-Tac-Toe Online Game (Client–Server)

This project is an implementation of an online Tic-Tac-Toe system written in Python.  
The purpose of the assignment is to improve programming skills and deepen understanding of:

- Transport layer (Layer 4 – TCP sockets)
- Application layer (Layer 5 – custom protocol design)
- Client–Server architecture
- Real-time communication between multiple clients

The server is capable of managing **multiple active Tic-Tac-Toe games in parallel**, while clients can create games, join existing games, and play in real time.

---

## 📁 Project Structure
tic_tac_toe/
│

├── game.py # Game logic (board, moves, win/draw detection)

├── game_manager.py # Managing multiple concurrent games

├── protocol.py # Communication utilities (send/recv)

├── server.py # Multi-client TCP server

└── client.py # CLI client with real-time updates


---

##  Features

###  Server
- Handles **multiple clients concurrently** using threading
- Supports **multiple parallel games**
- Manages game creation, joining, moves, and game state
- Detects **win**, **draw**, **invalid moves**, and illegal actions
- Sends updates to all players in real time
- Fully based on Python standard library (`socket`, `threading`)

###  Client
- Connects to the server via TCP
- Allows:
  - Listing available games
  - Creating a new game
  - Joining an existing game
  - Making moves
  - Receiving real-time updates
- Two-thread design:
  - One thread for user input
  - One thread for receiving and printing server messages

---

##  Requirements (As per assignment)

- Python 3.x
- No external libraries allowed — only standard Python libraries:
  - `socket`
  - `threading`
- Work on Windows, macOS, or Linux

---

## 🚀 How to Run

### 1. Start the server
```bash
python server.py

