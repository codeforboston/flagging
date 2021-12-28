import io
from typing import Any
from typing import List
from werkzeug.local import LocalProxy
from flask import g
from flask import Flask
from flask import has_app_context

from flask_caching import Cache as _Cache
from app.data.models.website_options import WebsiteOptions
from app.data.models.boathouse import Boathouse
from app.data.models.reach import Reach


file_cache: List[io.BytesIO] = []


class Cache(_Cache):
    """Implementation of the cache that also handles the cached_proxy objects.
    """

    app_context_variables: List[str]

    def __init__(self):
        super().__init__()
        self.app_context_variables = []

    def _clear_appcontext(self):
        if has_app_context():
            for i in self.app_context_variables:
                if i in g:
                    g.pop(i)

    def init_app(self, app: Flask, config=None) -> None:
        super().init_app(app=app, config=config)

        @app.teardown_appcontext
        def teardown_g(*args, **kwargs):
            self._clear_appcontext()

    def _close_files(self):
        for f in file_cache:
            f.close()
        del file_cache[:]

    def clear(self) -> None:
        # Clearing `g` shouldn't be necessary when cleaning the cache.
        # Still, better safe than sorry.
        self._clear_appcontext()
        self._close_files()
        super().clear()


cache = Cache()


def cached_proxy(func: callable, key: str) -> Any:
    """Factory for implementing a cache for a global object accessed via the
    Postgres database.
    """

    cache.app_context_variables.append(key)

    def _fetch():
        if has_app_context():
            active = g.get(key)
            if active:
                return active
            else:
                res = func()
                g.setdefault(key, res)
                return res
        else:
            res = func()
            return res

    return LocalProxy(_fetch)


website_options: WebsiteOptions = \
    cached_proxy(WebsiteOptions.get, key='website_options')  # type: ignore

boathouses: List[Boathouse] = \
    cached_proxy(Boathouse.get_all, key='boathouse_list')  # type: ignore

reaches: List[Reach] = \
    cached_proxy(Reach.get_all, key='reach_list')  # type: ignore
