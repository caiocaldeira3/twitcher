import dotenv
import json
import os
import requests
import websockets

import dataclasses as dc
import regex as re

from pathlib import Path

base_path = Path(__file__).resolve().parent
dotenv.load_dotenv(base_path / ".env", override=False)

user_regex = re.compile(r"^.*?(?=\!|\.tmi\.twitch\.tv)")

@dc.dataclass(init=True, repr=True)
class TwitchApi:

    base_url: str = dc.field(init=False, default="https://api.twitch.tv/helix/")
    client_id: str = dc.field(init=False, default=os.environ["CLIENT_ID"])
    client_secret: str = dc.field(init=False, default=os.environ["CLIENT_SECRET"])
    nick: str = dc.field(init=False, default=os.environ["NICK"])

    headers_client: dict = dc.field(init=False)
    headers_user: dict = dc.field(init=False)

    access_client: str = dc.field(init=False)
    access_user: str = dc.field(init=False)

    def __post_init__ (self) -> None:
        self.authenticate_client()
        self.headers_client = {
            "client-id": self.client_id,
            "Authorization": f"Bearer {self.access_client}"
        }

        # self._authenticate_user()
        # self.refresh_user()

    def authenticate_client (self) -> None:
        url = (
            f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}" +
            f"&client_secret={self.client_secret}&grant_type=client_credentials"
        )
        response = requests.post(url)

        self.access_client = response.json()["access_token"]

    def _authenticate_user (self) -> None:
        url = (
            f"https://id.twitch.tv/oauth2/authorize?response_type=code&client_id={self.client_id}" +
            "&redirect_uri=http://localhost&scope=chat:read chat:edit"
        )
        response = requests.get(url)
        print(response.url)

        code = input("Access Code: ")

        url = (
            f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}" +
            f"&client_secret={self.client_secret}&code={code}&grant_type=authorization_code" +
            "&redirect_uri=http://localhost"
        )
        response = requests.post(url)

        self.print_response(response)

        # Currently not Working
        os.environ["CHAT_ACCESS"] = response.json()["access_token"]
        os.environ["CHAT_REFRESH"] = response.json()["refresh_token"]

    def validate (self) -> None:
        url = "https://id.twitch.tv/oauth2/validate"
        response = requests.post(url, headers=self.headers_client)

        self.print_response(response)

    def refresh_user (self) -> None:
        url = (
            "https://id.twitch.tv/oauth2/token?grant_type=refresh_token" +
            f"&refresh_token={os.environ['CHAT_REFRESH']}&client_id={self.client_id}" +
            f"&client_secret={self.client_secret}"
        )
        response = requests.post(url)

        self.print_response(response)

        # Currently not Working
        os.environ["CHAT_ACCESS"] = response.json()["access_token"]
        os.environ["CHAT_REFRESH"] = response.json()["refresh_token"]

    async def connect_chat (self, channel: str) -> None:

        url = "wss://irc-ws.chat.twitch.tv:443"
        async with websockets.connect(url) as chat_socket:
            await chat_socket.send(f"PASS oauth:{os.environ['CHAT_ACCESS']}\r\n")
            await chat_socket.send(f"NICK {self.nick}\r\n")
            await chat_socket.send(f"JOIN #{channel}\r\n")

            while True:
                message = await chat_socket.recv()

                buffer = message.split(":")
                if "PING" in buffer[0]:
                    await chat_socket.send("PONG :tmi.twitch.tv\r\n")
                    continue

                context = buffer[1].split(" ")
                action = context[1]
                user = user_regex.match(context[0])

                if action == "PART":
                    continue
                elif action == "JOIN":
                    continue
                elif action == "PRIVMSG":
                    print(f"{user.group()}: {''.join(buffer[ 2 : ])}", end="")
                else:
                    continue

    def get_response (self, query: str) -> any:
        url = self.base_url + query

        response = requests.get(url, headers=self.headers)
        return response

    def print_response (self, response: any) -> None:
        response_json = response.json()

        print(json.dumps(response_json, indent=2))

    def user_streams_query (self, user_login: str) -> None:
        response = self.get_response(f"streams?user_login={user_login}")

        self.print_response(response)

    def user_query (self, user_login: str) -> None:
        response = self.get_response(f"streams?login={user_login}")

        self.print_response(response)

    def user_videos_query (self, user_id: str) -> None:
        response = self.get_response(f"streams?login={user_id}&first=50")

        self.print_response(response)
