import asyncio
import queue
import threading
import websockets

import dataclasses as dc
import tkinter as tk
import regex as re

context_regex = re.compile(
    r"(^@.*badges=(.*?);.*color=(.*?);.*emotes=(.*?);.*?):" +
    r"((.*?)!\6@\6\.tmi\.twitch\.tv (.*?) (.*?)) :(.*)"
)

@dc.dataclass(init=True, repr=False)
class TwitchChat:

    nick: str = dc.field(init=True)
    channel: str = dc.field(init=True)
    auth_access: str = dc.field(init=True)

    TEXT_COLOR: str = dc.field(init=True, default="#EAECEE")
    BG_COLOR: str = dc.field(init=True, default="#18181B")
    BG_GRAY: str = dc.field(init=True, default="#4B4B4F")

    FONT: str = dc.field(init=True, default="Helvetica 10")

    window: tk.Tk = dc.field(init=False, default=tk.Tk())
    receive_queue: list = dc.field(init=False, default=queue.Queue())
    send_queue: list = dc.field(init=False, default=queue.Queue())

    text_widget: tk.Text = dc.field(init=False)
    msg_entry: tk.Entry = dc.field(init=False)

    known_users: set = dc.field(init=False, default_factory=set)

    def __post_init__ (self) -> None:
        self.window.title(f"Twitch Chat - {self.channel}")
        self.window.resizable(width=True, height=True)
        self.window.configure(bg=self.BG_COLOR)

        # Text Widjet
        self.text_widget = tk.Text(
            self.window, bg=self.BG_COLOR, fg=self.TEXT_COLOR,
            font=self.FONT, padx=5, pady=8, spacing1=0, spacing2=1, spacing3=3
        )
        self.text_widget.place(relheight=0.970, relwidth=1)

        # Adding Default User Tag
        self.text_widget.tag_config(
            "DEFAULT_USER", font=self.FONT + " bold", foreground=self.TEXT_COLOR
        )

        # Bottom Label
        bottom_label = tk.Label(self.window, bg=self.BG_COLOR, height=20)
        bottom_label.place(relwidth=1, relheight=1, rely=0.968, )

        # Message Entry Box
        self.msg_entry = tk.Entry(
            bottom_label, bg=self.BG_GRAY, fg=self.TEXT_COLOR, font=self.FONT,
            borderwidth=5, relief=tk.FLAT
        )
        self.msg_entry.place(relwidth=1, relheight=0.03)
        self.msg_entry.focus()
        self.msg_entry.bind("<Return>", self.save_message)

    async def run (self) -> None:
        threading.Thread(target=self.irc_handler, daemon=True).start()

        self.event_handler()
        self.window.mainloop()

    def event_handler (self) -> None:
        try:
            msg, user, kwargs = self.receive_queue.get(block=False)
        except queue.Empty:
            pass
        else:
            self._insert_message(msg, user, **kwargs)

        self.window.after(150, self.event_handler)

    def irc_handler (self) -> None:
        asyncio.run(self._irc_handler())

    async def _irc_handler (self) -> None:
        url = "wss://irc-ws.chat.twitch.tv:443"
        async with websockets.connect(url) as chat_socket:

            await chat_socket.send(f"PASS oauth:{self.auth_access}\r\n")
            await chat_socket.send(f"NICK {self.nick}\r\n")
            await chat_socket.send(f"JOIN #{self.channel}\r\n")
            await chat_socket.send("CAP REQ :twitch.tv/tags\r\n")

            while True:
                consumer_task = asyncio.ensure_future(
                    self.receive_message(chat_socket)
                )
                producer_task = asyncio.ensure_future(
                    self.send_message(chat_socket)
                )
                done, pending = await asyncio.wait(
                    [ consumer_task, producer_task ],
                    return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()

    async def receive_message (self, chat_socket: object) -> None:
        message = await chat_socket.recv()

        print(message)

        buffer = message.split(":")
        if "PING" in buffer[0]:
            await chat_socket.send("PONG :tmi.twitch.tv\r\n")
            return

        parsed_message = context_regex.match(message)

        try:
            tags = parsed_message.group(1)
            context = parsed_message.group(5)

            action = parsed_message.group(7)

            if action == "PART":
                return
            elif action == "JOIN":
                return
            elif action == "PRIVMSG":
                user = parsed_message.group(6)

                kwargs = {}
                if parsed_message.group(3) != "":
                    kwargs["color"] = parsed_message.group(3)

                if parsed_message.group(2) != "":
                    kwargs["badges"] = parsed_message.group(2)

                if parsed_message.group(4) != "":
                    kwargs["emotes"] = parsed_message.group(4)

                txt = parsed_message.group(9)

                self.receive_queue.put((txt, user, kwargs))
            else:
                return

        except Exception:
            print("Message not parsed")

    async def send_message (self, chat_socket: object, message: str = None) -> None:
        if message is not None:
            await chat_socket.send(f"PRIVMSG #{self.channel} :{message}\r\n")
            return
        try:
            message = self.send_queue.get(block=False)
        except queue.Empty:
            await asyncio.sleep(150)
        else:
            await chat_socket.send(f"PRIVMSG #{self.channel} :{message}\r\n")
            self._insert_message(message + '\n', self.nick)

    def save_message (self, event: any) -> None:
        message = self.msg_entry.get()
        self.msg_entry.delete(0, tk.END)

        self.send_queue.put(message)

    def _insert_message(
        self, raw_msg: str, sender: str, color: str = None, emotes: str = None, badges: str = None
    ) -> None:
        if raw_msg == "":
            return
        if color is not None:
            self.text_widget.tag_config(sender, font=self.FONT + " bold", foreground=color)

            self.known_users.add(sender)
            tag = sender
        else:
            tag = "DEFAULT_USER"

        self.text_widget.configure(state=tk.NORMAL)

        self.text_widget.insert(tk.END, f"{sender}", tag)
        self.text_widget.insert(tk.END, f": {raw_msg}\n")

        self.text_widget.configure(state=tk.DISABLED)

        self.text_widget.see(tk.END)

if __name__ == "__main__":
    app = TwitchChat()
    app.run()
