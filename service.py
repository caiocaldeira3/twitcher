import asyncio
import sys

from twitch_api import TwitchApi

if __name__ == "__main__":

    try:
        twitch = TwitchApi()

        if len(sys.argv) < 2:
            asyncio.run(twitch.get_chat("patopapao"))
        else:
            asyncio.run(twitch.get_chat(sys.argv[1]))

    except (Exception):
        print("Api not loaded")
