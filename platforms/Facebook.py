"""
    Code to post to Facebook
    Originally written for Every Spongebob Frame In Order
"""
import math
import re
from io import BytesIO
from typing import Optional

import httpx
import yarl

from platforms.Platform import Platform

GRAPH_VERSION = "v14.0"


class Facebook(Platform):
    name: str = "Facebook"
    access_token: str
    page_id: str
    page_url: str
    page_name: str

    def __init__(self, access_token: str):
        self.access_token = access_token

    async def check_access_token(self):
        path = "/me"
        try:
            info = await self.request(
                path,
                query_params={
                    "fields": "id,name,can_post,link"
                })
        except Exception as e:
            raise RuntimeError(
                f"Failed to log into {self.name}. Please check your credentials and try again. Got Error: {e}")
        if info['can_post']:
            self.page_url = info['link']
            self.page_id = info['id']
            self.page_name = info['name']
        else:
            # todo: add link to docs here
            raise RuntimeError("You must grant all the permissions shown in the documentation.")

    @property
    def base_url(self) -> yarl.URL:
        return yarl.URL(f'https://graph.facebook.com/{GRAPH_VERSION}/')

    async def request(self, path: str, method: str = "GET", query_params: dict = None, json: Optional[dict] = None,
                      files: Optional[dict] = None) -> dict:
        if query_params is None:
            query_params = {}

        query_params.update({
            'access_token': self.access_token
        })
        async with httpx.AsyncClient(timeout=40) as client:
            url = self.base_url / path.lstrip("/") % query_params
            res = await client.request(method, str(url), json=json, files=files)
            res.raise_for_status()

            return res.json()

    async def post_frame(self, bt: BytesIO, message: Optional[str] = ""):
        await self.request(f"/{self.page_id}/photos", query_params={
            'message': message
        }, files={"frame": bt.read()}, method="POST")

    # maybe incorporate this eventually
    async def post_frame_url(self, url: str, message: Optional[str] = ""):
        posts = await self.request(f"/{self.page_id}/photos", query_params={
            'message': message,
            'url': url
        }, method="GET")

    async def best_of(self, number_of_posts: int = math.inf):
        next_url = f'/{self.page_id}/posts'
        posts = []
        query_params = {
            'fields': 'message,id,reactions.limit(0).summary(1).type(HAHA).as(haha),reactions.limit(0).summary(1).type(LIKE).as(like),reactions.limit(0).summary(1).type(LOVE).as(love),reactions.limit(0).summary(1).type(SAD).as(sad),reactions.limit(0).summary(1).type(ANGRY).as(angry),reactions.summary(1).limit(0).type(WOW).as(wow)',
            'limit': 100
        }
        while len(posts) < number_of_posts and next_url:
            new_posts = await self.request(next_url, query_params=query_params)
            if 'paging' not in new_posts:
                return posts

            if after_cur := new_posts.get('paging', {})['cursors']['after']:
                query_params['after'] = after_cur

            posts.extend(new_posts["data"])

            if len(posts) >= number_of_posts:
                posts = posts[:number_of_posts]

        update_posts = []
        for post in posts:
            regex = r"^[^ -]?Season ([0-9]+) Episode ([0-9]+) - Frame ([0-9]+) out of ([0-9]+)$"
            x = re.search(regex, post["message"], flags=re.M)
            if x:
                season = int(x.group(1))
                episode = int(x.group(2))
                frame = int(x.group(3))

                reacts = {
                    "wow": int(post["wow"]["summary"]["total_count"]),
                    "sad": int(post["sad"]["summary"]["total_count"]),
                    "like": int(post["like"]["summary"]["total_count"]),
                    "angry": int(post["angry"]["summary"]["total_count"]),
                    "love": int(post["love"]["summary"]["total_count"]),
                    "haha": int(post["haha"]["summary"]["total_count"])
                }
                print(post['message'], sum(reacts.values()))
                post_id = post["id"]

                frame_info = {
                    "season": season,
                    "episode": episode,
                    "frame": frame,
                    "post_id": post_id,
                    "reacts": reacts
                }
                update_posts.append(frame_info)

        return update_posts
