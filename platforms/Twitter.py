"""
    Code to post to Facebook
    Originally written for Every Spongebob Frame In Order
"""
from io import BytesIO
from typing import Optional

import tweepy

from lib.Platform import Platform


class Twitter(Platform):
    name: str = "Twitter"
    access_token: str
    page_id: str
    page_url: str
    page_name: str

    def __init__(self, consumer_key: str, consumer_secret: str, access_token: str, access_token_secret: str):
        self.access_token = access_token
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth, wait_on_rate_limit=True)

    async def check_access_token(self):
        try:
            self.api.verify_credentials()
        except Exception as e:
            raise RuntimeError("Error while logging in to Twitter - Please verify your credentials")

    async def post_frame(self, bt: BytesIO, message: Optional[str] = ""):
        upload = self.api.media_upload(file=bt, filename='frame.png')
        self.api.update_status(media_ids=[upload.media_id_string], status=f"{message}")
