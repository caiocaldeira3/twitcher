import dotenv
import json
import os
import requests

import dataclasses as dc

from pathlib import Path

base_path = Path(__file__).resolve().parent
dotenv.load_dotenv(base_path / ".env", override=False)

@dc.dataclass(init=True, repr=True)
class TwitchApi:

    base_url: str = dc.field(init=False, default="https://api.twitch.tv/helix/")
    client_id: str = dc.field(init=False, default=os.environ["CLIENT_ID"])
    client_secret: str = dc.field(init=False, default=os.environ["CLIENT_SECRET"])
    headers: dict = dc.field(init=False)

    oauth: str = dc.field(init=False)

    def __post_init__ (self) -> None:
        self.authenticate()
        self.headers = {
            "client-id": self.client_id,
            "Authorization": f"Bearer {self.oauth}"
        }

    def authenticate (self) -> None:
        url = (
            f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}" +
            f"&client_secret={self.client_secret}&grant_type=client_credentials"
        )

        response = requests.post(url)
        self.oauth = response.json()["access_token"]

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

    def userquery (self, user_login: str) -> None:
        response = self.get_response(f"streams?login={user_login}")

        self.print_response(response)

    def user_videos_query (self, user_id: str) -> None:
        response = self.get_response(f"streams?login={user_id}&first=50")

        self.print_response(response)
