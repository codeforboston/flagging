from typing import Any
from typing import List
from werkzeug.local import LocalProxy
from flask import g

from app.data.models.website_options import WebsiteOptions
from app.data.models.boathouse import Boathouse
from app.data.models.reach import Reach
from app.data.database import cache


def request_context_object(func: callable, key: str) -> Any:
    """Factory for implementing a multilayer cache for a global object accessed
    via the Postgres database.

    The object is cached both in memory during the request context, and in the
    Redis layer. So when the request dies, the object still persists in Redis,
    and will be reloaded into a new request context.
    """

    def _fetch():
        active = g.get(key)
        if active:
            return active
        elif cache.cache.has(key):
            res = cache.get(key)
            g.setdefault(key, res)
            return res
        else:
            res = func()
            cache.set(key, res)
            g.setdefault(key, res)
            return res

    return LocalProxy(_fetch)


website_options: WebsiteOptions = \
    request_context_object(WebsiteOptions.get, key='website_options')  # type: ignore

boathouses: List[Boathouse] = \
    request_context_object(Boathouse.get_all, key='boathouse_list')  # type: ignore

reaches: List[Reach] = \
    request_context_object(Reach.get_all, key='reach_list')  # type: ignore
