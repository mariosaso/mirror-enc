# main.py
import threading
#import sys
from modules.gui import GUI
from modules.__init__ import BANNER
from modules.chat_service import ChatServer, ChatClient
from modules.prompts import mode_config, server_config, client_config

def run_server(host, port, password):
    server = ChatServer(host, port, password)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    print(f"[+] Server started on {host}:{port}")

    gui = GUI(server, server.gui_queue, mode="server")
    try:
        gui.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[!] GUI error: {e}")
    finally:
        server.stop()
        server_thread.join(timeout=2)
        print("[+] Server stopped.")

def run_client(host, port, password, nickname):
    client = ChatClient(host, port, password, nickname)
    try:
        client.start()
        print(f"[+] Connected to {host}:{port} as {nickname}")

        gui = GUI(client, client.gui_queue, mode="client", nickname=nickname)
        gui.run()
    except (RuntimeError, KeyboardInterrupt):
        pass
    finally:
        client.stop()
        print("[+] Client disconnected.")

def main():
    try:
        print(BANNER)
        mode = mode_config()
        if mode == "server":
            host, port, password = server_config()
            print()
            run_server(host, port, password)
        else:
            host, port, password, nickname = client_config()
            print()
            run_client(host, port, password, nickname)
    except:
        print("[+] Exiting...")

if __name__ == "__main__":
    main()
