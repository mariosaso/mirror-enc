# chat_service.py
import queue
import threading
from modules.tcp_service import TCPServer, TCPClient
from cryptography.fernet import InvalidToken

#################### Server Side ####################

class ChatServer(TCPServer):
    def __init__(self, host, port, password=None):
        super().__init__(host, port)
        self.password = password
        self.gui_queue = queue.Queue()

    def start(self):
        try:
            self.accept()
        except OSError:
            pass
        except Exception as e:
            print(f"[!] Server encountered fatal error: {e}")
        finally:
            self.stop()

    def send_message(self, message):
        """Called by server GUI to send a server-originated message."""
        formatted = f"[SERVER]: {message}"
        self.broadcast(formatted)
        self.gui_queue.put(formatted)

    def broadcast(self, message, sender_socket=None):
        """Safely send message to all clients, removing any that fail."""
        with self.lock:
            for client in list(self.clients):
                sock = client['socket']
                key = client['session_key']
                if sock is not sender_socket:
                    try:
                        self._send(message, sock, sym_encryption_key=key)
                    except Exception as e:
                        try:
                            self.remove_client(client)
                        except Exception:
                            pass

    def _get_session_key(self, client_socket):
        with self.lock:
            for c in self.clients:
                if c['socket'] == client_socket:
                    return c.get('session_key')
        return None

    def _is_nick_in_use(self, nickname):
        with self.lock:
            return any(c.get('nickname') == nickname for c in self.clients)

    def _authenticate(self, client_socket, session_key):
        # Password check
        if self.password:
            self._send("PWD_REQ", client_socket, sym_encryption_key=session_key)
            resp = self._receive(client_socket, sym_encryption_key=session_key)
            if not resp.startswith("PWD:") or resp.split(":",1)[1] != self.password:
                self._send("PWD_ERR", client_socket, sym_encryption_key=session_key)
                return False, None
            self._send("PWD_OK", client_socket, sym_encryption_key=session_key)

        # Nickname check
        self._send("NICK_REQ", client_socket, sym_encryption_key=session_key)
        resp = self._receive(client_socket, sym_encryption_key=session_key)
        if not resp.startswith("NICK:"):
            self._send("NICK_ERR", client_socket, sym_encryption_key=session_key)
            return False, None
        nickname = resp.split(":",1)[1]
        if self._is_nick_in_use(nickname):
            self._send("NICK_TAKEN", client_socket, sym_encryption_key=session_key)
            return False, None
        self._send("NICK_OK", client_socket, sym_encryption_key=session_key)

        # Store nickname
        with self.lock:
            for c in self.clients:
                if c['socket'] == client_socket:
                    c['nickname'] = nickname
                    break

        return True, nickname

    def _handle_client(self, client_socket, addr):
        session_key = self._get_session_key(client_socket)
        ok, nickname = self._authenticate(client_socket, session_key)
        if not ok:
            try: client_socket.close()
            except: pass
            return

        join_msg = f"{nickname} has joined the chat"
        self.broadcast(join_msg)
        self.gui_queue.put(join_msg)

        try:
            while self.is_running:
                try:
                    msg = self._receive(client_socket, sym_encryption_key=session_key)
                except (ConnectionError, Exception):
                    break
                if not msg:
                    break

                formatted = f"[{nickname}]: {msg}"
                self.broadcast(formatted)
                self.gui_queue.put(formatted)

        finally:
            leave_msg = f"{nickname} has left the chat"
            with self.lock:
                # remove client record
                for c in list(self.clients):
                    if c['socket'] == client_socket:
                        self.clients.remove(c)
                        break
            self.broadcast(leave_msg)
            self.gui_queue.put(leave_msg)
            try: client_socket.close()
            except: pass

    def on_client_connect(self, client_socket, addr):
        threading.Thread(
            target=self._handle_client,
            args=(client_socket, addr),
            daemon=True
        ).start()


#################### Client Side ####################

class ChatClient(TCPClient):
    def __init__(self, host, port, password, nickname):
        super().__init__(host, port)
        self.password = password
        self.nickname = nickname
        self.gui_queue = queue.Queue()

    def start(self):
        try:
            self.connect()
            self.negotiate_nickname()
        except Exception as e:
            print(f"[!] Failed to authenticate: {e}")
            self.stop()
            raise
        # spawn listener
        threading.Thread(target=self._receive_messages, daemon=True).start()        

    def negotiate_nickname(self):
        # 1) Password challenge
        preliminary = self._receive(self.client_socket, sym_encryption_key=self.session_key)
        if preliminary == "PWD_REQ":
            self._send(f"PWD:{self.password}", self.client_socket, sym_encryption_key=self.session_key)
            resp = self._receive(self.client_socket, sym_encryption_key=self.session_key)
            if resp == "PWD_ERR":
                raise RuntimeError("Wrong password")
            if resp != "PWD_OK":
                raise RuntimeError(f"Authentication error: {resp}")

        # 2) Nickname challenge
        resp = self._receive(self.client_socket, sym_encryption_key=self.session_key)
        if resp != "NICK_REQ":
            raise RuntimeError(f"Unexpected server response: {resp}")

        self._send(f"NICK:{self.nickname}", self.client_socket, sym_encryption_key=self.session_key)
        resp = self._receive(self.client_socket, sym_encryption_key=self.session_key)
        if resp == "NICK_TAKEN":
            raise RuntimeError("This nickname is taken")
        if resp != "NICK_OK":
            raise RuntimeError(f"Nickname error: {resp}")

    def send_message(self, message):
        try:
            self._send(message, self.client_socket, sym_encryption_key=self.session_key)
        except Exception as e:
            print(f"[!] Send error: {e}")
            self.stop()
            self.gui_queue.put("** Connection error. Disconnected **")

    def _receive_messages(self):
        try:
            while self.is_running:
                try:
                    msg = self._receive(
                        self.client_socket,
                        sym_encryption_key=self.session_key
                    )
                    if not msg:
                        # clean shutdown from server
                        raise ConnectionError("Server closed connection")
                    self.gui_queue.put(msg)

                except (ConnectionError, InvalidToken):
                    # normal close (or decryption failure) → notify GUI, then exit
                    self.is_running = False
                    self.gui_queue.put("** Connection closed by server **")
                    break

                except Exception as e:
                    # any other error → notify GUI, then exit silently
                    self.is_running = False
                    self.gui_queue.put(f"** Unexpected error: {e} **")
                    break
        except Exception:
            # catch *anything* that slipped through to prevent traceback
            pass