from abc import ABC, abstractmethod
from io import BytesIO
from typing import Optional

import yarl


class Platform(ABC):
    name: str
    access_token: str
    page_url: str

    @abstractmethod
    def check_access_token(self):
        raise NotImplementedError()

    @property
    def base_url(self) -> yarl.URL:
        raise NotImplementedError()

    def request(self, path: str, method: str = "GET", json: Optional[dict] = None):
        raise NotImplementedError()

    @abstractmethod
    def post_frame(self, frame: BytesIO, message: str):
        raise NotImplementedError()

    def best_of(self, param):
        pass
