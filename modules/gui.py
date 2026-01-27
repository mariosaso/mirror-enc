# gui.py
import tkinter as tk
from tkinter import scrolledtext

class GUI:
    def __init__(self, chat_server, gui_queue, mode, nickname=""):
        self.chat_server = chat_server
        self.gui_queue = gui_queue
        self.mode = mode

        self.window = tk.Tk()
        title = "[server]" if mode == "server" else f"[client: {nickname}]"
        self.window.title(f"mirror-enc {title}")

        self.text_area = scrolledtext.ScrolledText(
            self.window, wrap=tk.WORD, width=50, height=15, state=tk.DISABLED
        )
        self.text_area.grid(column=0, row=0, padx=15, pady=15, columnspan=2)

        self.message_entry = tk.Entry(self.window, width=40)
        self.message_entry.grid(column=0, row=1, padx=15, pady=10, sticky="w")
        self.message_entry.bind("<Return>", self.handle_send)

        self.send_button = tk.Button(self.window, text="Send", command=self.handle_send)
        self.send_button.grid(column=1, row=1, padx=10, pady=10, sticky="e")

        # Start polling the queue
        self.window.after(100, self.process_gui_queue)

    def append_to_area(self, text):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.yview(tk.END)

    def handle_send(self, event=None):
        msg = self.message_entry.get().strip()
        if msg:
            self.chat_server.send_message(msg)
            self.message_entry.delete(0, tk.END)

    def process_gui_queue(self):
        while not self.gui_queue.empty():
            msg = self.gui_queue.get_nowait()
            self.append_to_area(msg)

            # If client loses its server connection, close the GUI automatically
            if self.mode == "client" and msg == "** Connection closed by server **":
                # give the user a moment to read the message
                self.window.after(100, self.window.quit)
                return

        self.window.after(100, self.process_gui_queue)

    def run(self):
        self.window.mainloop()
