"""
    Code to post to Facebook
    Originally written for Every Spongebob Frame In Order
"""
from io import BytesIO
from typing import Optional

import discord as discord

from platforms.Platform import Platform


class DiscordClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')


class Discord(Platform):
    name: str = "Discord"
    access_token: str
    page_id: str
    page_url: str
    page_name: str

    async def __aenter__(self):
        self.channel = await self.client.fetch_channel(self.channel_id)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()

    def __init__(self, access_token: str, channel_id: int):
        self.access_token = access_token
        self.channel_id = channel_id
        self.client = DiscordClient()

    async def check_access_token(self):
        try:
            await self.client.login(token=self.access_token, bot=True)
            self.channel = await self.client.fetch_channel(self.channel_id)
        except Exception as e:
            raise RuntimeError("Error while logging in to Discord - Please verify your credentials")

    async def post_frame(self, bt: BytesIO, message: Optional[str] = ""):
        await self.channel.send(content=message, file=discord.File(bt, 'frame.png'))
