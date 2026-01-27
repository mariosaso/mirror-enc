# prompts.py
from InquirerPy import inquirer

def mode_config():
    return inquirer.select(
        message="Select mode:",
        choices=[{"name":"Server","value":"server"},{"name":"Client","value":"client"}],
        default="server"
    ).execute()

def server_config():
    host = inquirer.text(message="Server host:", default="localhost", validate=lambda t:bool(t.strip())).execute()
    port = int(inquirer.text(message="Server port:", default="4444", validate=lambda t:t.isdigit() and 1<=int(t)<=65535).execute())
    password = inquirer.secret(message="Enter password:", validate=lambda t:bool(t.strip())).execute()
    return host, port, password

def client_config():
    host = inquirer.text(message="Server host to connect to:", validate=lambda t:bool(t.strip())).execute()
    port = int(inquirer.text(message="Server port to connect to:", default="4444", validate=lambda t:t.isdigit() and 1<=int(t)<=65535).execute())
    password = inquirer.secret(message="Enter password:", validate=lambda t:bool(t.strip())).execute()
    nickname = inquirer.text(message="Your nickname:", validate=lambda t:bool(t.strip())).execute()
    return host, port, password, nickname
