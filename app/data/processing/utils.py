import typing as t
from functools import wraps
import os
import pandas as pd
from flask import current_app


F = t.TypeVar('F', bound=t.Callable[..., pd.DataFrame])


def mock_source(filename: str) -> t.Callable[[F], F]:
    """
    This is what the `USE_MOCK_DATA` config option is used for. If turned on,
    then this returns data from the "data store" rather than live data. This is
    useful for unit-tests or demoing the site without needing to have
    credentials.

    This function is a decorator.
    """
    def _decorator(func: F) -> F:
        @wraps(func)
        def _wrapper(*args, **kwargs):
            if current_app.config['USE_MOCK_DATA']:
                fpath = os.path.join(
                    current_app.config['DATA_STORE'], filename
                )
                df = pd.read_pickle(fpath)
                return df
            else:
                return func(*args, **kwargs)
        return _wrapper
    return _decorator
