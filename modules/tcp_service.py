import socket
import threading
from modules.crypto import *


def _recv_all(sock, n):
    """
    Receive exactly n bytes from the socket or raise ConnectionError if the
    connection is closed prematurely.
    """
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            raise ConnectionError("Socket connection broken")
        data += packet
    return data


class TCPServer:
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.clients = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        # allow accept() to time out periodically so we can check is_running
        self.server_socket.settimeout(1.0)
        self.lock = threading.Lock()
        self.server_private_key, self.server_public_key = generate_rsa_keypair()
        self.server_public_pem = serialize_public_key(self.server_public_key)
        self.is_running = True

    def _send(self, data, target_socket, sym_encryption_key=None, asym_encryption_key=None):
        # Prepare payload
        if isinstance(data, str):
            payload = data.encode()
        elif isinstance(data, bytes):
            payload = data
        else:
            raise TypeError("Data must be bytes or str")

        # Encrypt if needed
        if sym_encryption_key:
            payload = symmetric_encrypt(sym_encryption_key, payload)
        elif asym_encryption_key:
            payload = asymmetric_encrypt(asym_encryption_key, payload)

        # Prefix with 4-byte length header (big-endian)
        length = len(payload)
        header = length.to_bytes(4, 'big')
        target_socket.sendall(header + payload)

    def _receive(self, target_socket, sym_encryption_key=None, asym_decryption_key=None):
        # Read 4-byte length header
        header = _recv_all(target_socket, 4)
        length = int.from_bytes(header, 'big')
        # Read the full payload
        body = _recv_all(target_socket, length)

        # Decrypt if needed
        if sym_encryption_key:
            body = symmetric_decrypt(sym_encryption_key, body)
        elif asym_decryption_key:
            body = asymmetric_decrypt(asym_decryption_key, body)

        return body.decode()

    def accept(self):
        while self.is_running:
            try:
                client_sock, addr = self.server_socket.accept()
            except socket.timeout:
                continue
            # handshake: send public key, receive session key
            self._send(self.server_public_pem.decode(), client_sock)
            sess = self._receive(client_sock, asym_decryption_key=self.server_private_key)
            with self.lock:
                self.clients.append({
                    'socket': client_sock,
                    'address': addr,
                    'session_key': sess
                })
            self.on_client_connect(client_sock, addr)

    def broadcast(self, message, sender_socket=None):
        with self.lock:
            for c in self.clients:
                sock = c['socket']
                key = c['session_key']
                if sock != sender_socket:
                    self._send(message, sock, sym_encryption_key=key)

    def remove_client(self, client):
        client['socket'].shutdown(socket.SHUT_RDWR)
        client['socket'].close()
        self.clients.remove(client)

    def stop(self):
        self.is_running = False
        with self.lock:
            for c in list(self.clients):
                self.remove_client(c)
        self.server_socket.close()

    def on_client_connect(self, client_socket, addr):
        pass  # to be overridden


class TCPClient:
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.session_key = generate_symmetric_key()
        self.is_running = True

    def _send(self, data, target_socket, sym_encryption_key=None, asym_encryption_key=None):
        # Prepare payload
        if isinstance(data, str):
            payload = data.encode()
        elif isinstance(data, bytes):
            payload = data
        else:
            raise TypeError("Data must be bytes or str")

        # Encrypt if needed
        if sym_encryption_key:
            payload = symmetric_encrypt(sym_encryption_key, payload)
        elif asym_encryption_key:
            payload = asymmetric_encrypt(asym_encryption_key, payload)

        # Prefix with 4-byte length header (big-endian)
        length = len(payload)
        header = length.to_bytes(4, 'big')
        target_socket.sendall(header + payload)

    def _receive(self, target_socket, sym_encryption_key=None, asym_decryption_key=None):
        # Read 4-byte length header
        header = _recv_all(target_socket, 4)
        length = int.from_bytes(header, 'big')
        # Read the full payload
        body = _recv_all(target_socket, length)

        # Decrypt if needed
        if sym_encryption_key:
            body = symmetric_decrypt(sym_encryption_key, body)
        elif asym_decryption_key:
            body = asymmetric_decrypt(asym_decryption_key, body)

        return body.decode()

    def connect(self):
        # Receive server public key
        pub_pem = self._receive(self.client_socket)
        server_pub = load_public_key(pub_pem.encode('utf-8'))
        # Send our generated symmetric key encrypted with server's public RSA key
        self._send(self.session_key, self.client_socket, asym_encryption_key=server_pub)

    def stop(self):
        self.is_running = False
        # avoid shutdown/close on an already-closed socket
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.client_socket.close()
        except OSError:
            pass
