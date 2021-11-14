from abc import ABCMeta

from celery import Task
from celery import Celery as _Celery

from flask import Flask

from app.data.processing.hobolink import DEFAULT_HOBOLINK_EXPORT_NAME
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.usgs import get_live_usgs_data


class WithAppContextTask(Task, metaclass=ABCMeta):
    def __call__(self, *args, **kwargs):
        with self.app.flask_app.app_context():
            return super().__call__(*args, **kwargs)


class Celery(_Celery):
    task_cls = WithAppContextTask
    flask_app: Flask = None


celery_app = Celery(__name__)


def init_celery(app: Flask):
    celery_app.flask_app = app
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )


@celery_app.task
def live_hobolink_task(export_name: str = DEFAULT_HOBOLINK_EXPORT_NAME) -> dict:
    return get_live_hobolink_data(export_name=export_name).to_dict(orient='records')


@celery_app.task
def live_usgs_data_task(days_ago: int = 14) -> dict:
    return get_live_usgs_data(days_ago=days_ago).to_dict(orient='records')
