import dotenv
import fileinput
import json
import os
import requests

import dataclasses as dc
import regex as re

from pathlib import Path

base_path = Path(__file__).resolve().parent

import twitch_chat

dotenv.load_dotenv(base_path / ".env", override=False)

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
        self.refresh_user()

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

        self._update_enviroment("CHAT_ACCESS", response.json()["access_token"])
        self._update_enviroment("CHAT_REFRESH", response.json()["refresh_token"])

    def _update_enviroment (self, key: str, value: str) -> None:
        environ_regex = re.compile(f"(?<={key}=).*")

        with fileinput.FileInput(".env", inplace=True, backup=".bak") as env:
            for line in env:
                print(environ_regex.sub(f"\"{value}\"", line), end="")

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

        self._update_enviroment("CHAT_ACCESS", response.json()["access_token"])
        self._update_enviroment("CHAT_REFRESH", response.json()["refresh_token"])

    async def get_chat (self, channel: str = None) -> None:
        if channel is None:
            channel = self.nick

        twt_chat = twitch_chat.TwitchChat(self.nick, channel, os.environ["CHAT_ACCESS"])

        await twt_chat.run()

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
