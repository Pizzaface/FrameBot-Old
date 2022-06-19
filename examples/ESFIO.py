import httpx
import yarl

from lib.FrameBot import FrameBot
from platforms.Platform import Platform

BASE_URL = ''
API_KEY = ''
BEST_OF_POST_URL = ''


class ESFIO(FrameBot):
    _min_frame: int = None
    _max_frame: int = None
    show: str = "spongebob"
    api_key: str = API_KEY

    """

    ESFIO - Facebook
    Based on the bot used for Every Spongebob Frame In Order

    """

    def __init__(self, platforms: list[Platform], frames_per_cycle=25, sleep_secs=3600):
        super().__init__(platforms, frames_per_cycle, sleep_secs)

    @property
    def folder_template(self) -> str:
        return "/S{s}E{e}"

    @property
    def filename_template(self) -> str:
        return self.folder_template + "/{f}.png"

    def db_path_template(self):
        return "{self.show}-{self.platform}"

    @property
    def authentication_headers(self):
        return {"x-api-key": self.api_key}

    async def get_frame_count(self, season=None, episode=None):
        if season is None:
            season = self.season

        if episode is None:
            episode = self.episode

        if self.base_url is not None:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                url = (
                        self.base_url
                        / self.folder_template.format(
                    s=str(season).zfill(2), e=str(episode).zfill(2)
                ).lstrip("/")
                        / "counts"
                )
                req = await client.get(str(url))

                if req.status_code == 500:
                    raise RuntimeError("Couldn't access frame counts.")

                if req.status_code == 404:
                    data = req.json()
                    if data["info"] == "go to next season":
                        self.season += 1
                        self.episode = 1
                        self.frame = 0
                        return await self.get_frame_count()

                data = req.json()
                self._min_frame = data["first"]
                self._max_frame = data["last"]

                if self.frame == 0:
                    self.frame = self._min_frame

                return self._min_frame, self._max_frame

        return None

    def error_webhook(self, message: str) -> dict:
        """
        The information to call the error webhook.
        Expects a dict in the form of self.call_webhook's kwargs
        {
            "url": <yarl.URL>,
            "query_params": {
                "foo": "bar"
            },
            "json": {
                "foo": "bar"
            }
        }
        :return: dict
        """
        # todo: update with HASSIO URL
        raise {"url": yarl.URL(), "json": {"status": "ERROR!", "message": message}}

    @property
    def base_url(self) -> yarl.URL:
        return yarl.URL(BASE_URL)

    @property
    def message_template(self):
        return "Season {s} Episode {e} - Frame {f} out of {max}"

    async def handle_best_of(self, posts=None):
        async with httpx.AsyncClient(timeout=40, follow_redirects=True) as client:
            for plat in self.platforms:
                if posts is None:
                    posts = await plat.best_of(500)

                if hasattr(plat, "best_of"):
                    url = BEST_OF_POST_URL

                    best_frame = max(posts, key=lambda x: sum(x["reacts"].values()))
                    best_frame = await self.get_frame(
                        best_frame["season"], best_frame["episode"], best_frame["frame"]
                    )
                    advertised_posts = filter(
                        lambda x: sum(x["reacts"].values()) >= 200, posts
                    )

                    req = await client.request(url=url, json=posts, method="POST", headers=self.authentication_headers)

                    if req.status_code == 201:
                        print(req.text)
                        message = "~Updating Best Of Archives~\nHere are some of the highlights!\n"

                        for post in advertised_posts:
                            p_s = post["season"]
                            p_e = post["episode"]
                            message += (
                                    "  - "
                                    + self.message_template.replace(' out of {max}',
                                                                    f' with {sum(post["reacts"].values())} reacts!').format(
                                s=p_s, e=p_e, f=post["frame"])
                                    + "\n"
                            )
                    else:
                        await self.call_webhook(
                            self.error_webhook("Failed to Update Best Of.")
                        )

        await plat.post_frame(best_frame, message=message)
