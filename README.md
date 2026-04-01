# mirror-enc

An encrypted TCP chat application with GUI, built in Python.

## Overview

mirror-enc is a lightweight client-server chat system that supports:

- End-to-end encrypted communication
- Multi-client chat rooms
- Password-protected server access
- Unique nickname system
- Simple graphical interface (Tkinter)

The project is designed to be modular, extensible, and easy to understand.

---

## Features

- RSA-based key exchange
- Symmetric encryption using Fernet (AES + HMAC)
- Threaded server with multiple clients
- Real-time GUI updates via queue system
- Clean separation of:
  - networking (TCP)
  - encryption
  - chat logic
  - UI

---

## Architecture

```
mirror-enc/
│
├── main.py              # Entry point
├── chat_service.py      # Chat logic (server/client)
├── tcp_service.py       # Low-level TCP + handshake
├── crypto.py            # Encryption utilities
├── gui.py               # Tkinter GUI
├── prompts.py           # CLI configuration
└── __init__.py          # Banner / metadata
```

### Flow

1. Server starts and listens for connections
2. Client connects
3. RSA handshake exchanges a symmetric key
4. Authentication (password + nickname)
5. Encrypted messages are exchanged using Fernet

---

## Installation

### Requirements

- Python 3.8+
- pip

### Install dependencies

```bash
pip install cryptography InquirerPy
```

---

## Usage

### Run the application

```bash
python mirror-enc.py
```

### Select mode

You will be prompted to choose:

- Server
- Client

---

## Server Mode

You will be asked:

- Host (default: localhost)
- Port (default: 4444)
- Password

Example:

```
Host: localhost
Port: 4444
Password: ********
```

---

## Client Mode

You will be asked:

- Server host
- Server port
- Password
- Nickname

Example:

```
Host: localhost
Port: 4444
Password: ********
Nickname: Mario
```

---

## Encryption Details

### Key Exchange

- RSA (2048 bits) is used for secure key exchange
- The client generates a symmetric key
- The key is encrypted with the server public key

### Message Encryption

- All messages are encrypted using Fernet
- Fernet provides:
  - AES encryption
  - HMAC authentication

---

## GUI

The application uses Tkinter:

- Chat display area
- Message input field
- Send button
- Auto-scroll
- Real-time updates via queue

---

## Important Notes

- Each nickname must be unique
- Server password is required for authentication
- Messages are encrypted during transmission only (no persistence)
- GUI closes automatically when the connection is lost (client mode)

---

## Known Limitations

- No message history
- No reconnection logic
- Basic error handling
- No persistence layer
- Server without password is not fully supported

---

## Future Improvements

- Reconnection support
- Message history
- File transfer
- Better error handling
- Config file support
- UI improvements
- Plugin architecture

---

## Example

Run server:

```bash
python mirror-enc.py
```

Select:
```
Server
```

Run client (in another terminal):

```bash
python mirror-enc.py
```

Select:
```
Client
```

Start chatting securely.

---

## Author

Mario Saso   
https://github.com/mariosaso

---

## License

This project uses the GPLv3 license
