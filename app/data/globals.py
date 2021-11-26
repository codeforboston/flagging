from typing import Any
from typing import List
from werkzeug.local import LocalProxy
from flask import g

from flask_caching import Cache as _Cache
from app.data.models.website_options import WebsiteOptions
from app.data.models.boathouse import Boathouse
from app.data.models.reach import Reach


class Cache(_Cache):
    """Implementation of the cache that also handles the cached_proxy objects.
    """

    app_context_variables: List[str]

    def __init__(self):
        super().__init__()
        self.app_context_variables = []

    def clear(self) -> None:
        for i in self.app_context_variables:
            if i in g:
                g.pop(i)
        super().clear()


cache = Cache()


def cached_proxy(func: callable, key: str) -> Any:
    """Factory for implementing a cache for a global object accessed via the
    Postgres database.
    """

    cache.app_context_variables.append(key)

    def _fetch():
        active = g.get(key)
        if active:
            return active
        else:
            res = func()
            g.setdefault(key, res)
            return res

    return LocalProxy(_fetch)


website_options: WebsiteOptions = \
    cached_proxy(WebsiteOptions.get, key='website_options')  # type: ignore

boathouses: List[Boathouse] = \
    cached_proxy(Boathouse.get_all, key='boathouse_list')  # type: ignore

reaches: List[Reach] = \
    cached_proxy(Reach.get_all, key='reach_list')  # type: ignore
