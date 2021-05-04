from twitch_api import TwitchApi

if __name__ == "__main__":

    try:
        twitch = TwitchApi()

        twitch.user_streams_query("gaules")

    except (Exception):
        print("Api not loaded")
