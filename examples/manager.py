import asyncio

from ESFIO import ESFIO
from platforms.Discord import Discord
from platforms.Facebook import Facebook
from platforms.Twitter import Twitter

FACEBOOK_ACCESS_TOKEN = ''

TWITTER_AUTH_INFO = {
    "consumer_key": "",
    "consumer_secret": "",
    "access_token": "",
    "access_token_secret": ""
}

DISCORD_AUTH = {
    "channel_id": 1234567890,  # Input the channel ID you want to post in here
    "access_token": ""  # Your Bot's Access Token
}


async def run_bots():
    fb_platform = Facebook(FACEBOOK_ACCESS_TOKEN)
    twitter_platform = Twitter(**TWITTER_AUTH_INFO)
    discord_platform = Discord(**DISCORD_AUTH)

    # Preform a check to see that we can post within the platform
    # This doesn't post anything, just runs a check to log in.
    await fb_platform.check_access_token()
    await twitter_platform.check_access_token()
    await discord_platform.check_access_token()

    # Initialize your Social Media Bot with it's platforms
    esfio = ESFIO(platforms=[fb_platform, twitter_platform, discord_platform], frames_per_cycle=25)

    # Run through the platforms, collecting data about the previous frames posted
    await esfio.handle_best_of()

    # Loop through each platform again, loading the database for each one, and posting the new frames
    await esfio.post_content()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_bots())
