import asyncio
from twitch_api import TwitchApi

if __name__ == "__main__":

    try:
        twitch = TwitchApi()
        asyncio.run(twitch.connect_chat("swimstrim"))
    except (Exception):
        print("Api not loaded")
