import logging
from abc import ABCMeta
from typing import Any
from typing import Dict
from typing import List
from typing import TypeVar

from celery import Celery as _Celery
from celery import Task
from celery.signals import task_postrun
from celery.signals import task_prerun
from celery.utils.log import get_task_logger
from flask import Flask


RecordsType = TypeVar('RecordsType', bound=List[Dict[str, Any]])


class WithAppContextTask(Task, metaclass=ABCMeta):
    def __call__(self, *args, **kwargs):
        with self.app.flask_app.app_context():
            return super().__call__(*args, **kwargs)


class Celery(_Celery):
    task_cls = WithAppContextTask
    flask_app: Flask = None

    def health(self) -> None:
        assert self.control.inspect().ping() is not None, (
            'It looks like Celery is not ready.'
            ' Open up a second terminal and run the command:'
            ' `flask celery worker`'
        )


celery_app = Celery(__name__)

logger: logging.Logger = get_task_logger(__name__)
logger.setLevel(logging.INFO)


def init_celery(app: Flask):
    celery_app.flask_app = app
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )


@task_prerun.connect
def task_starting_handler(*args, **kwargs):
    logger.info('Starting task.')


@task_postrun.connect
def task_finished_handler(*args, **kwargs):
    logger.info('Finished task.')


@celery_app.task
def live_hobolink_data_task(*args, **kwargs) -> RecordsType:
    from app.data.processing.hobolink import get_live_hobolink_data
    df = get_live_hobolink_data(*args, **kwargs)
    return df.to_dict(orient='records')


@celery_app.task
def live_usgs_data_task(*args, **kwargs) -> RecordsType:
    from app.data.processing.usgs import get_live_usgs_data
    df = get_live_usgs_data(*args, **kwargs)
    return df.to_dict(orient='records')


@celery_app.task
def combine_data_task(*args, **kwargs) -> RecordsType:
    from app.data.processing.core import combine_job
    df = combine_job(*args, **kwargs)
    return df.to_dict(orient='records')


@celery_app.task
def prediction_task(*args, **kwargs) -> RecordsType:
    from app.data.processing.core import predict_job
    df = predict_job(*args, **kwargs)
    return df.to_dict(orient='records')


@celery_app.task
def update_db_task() -> None:
    from app.data.processing.core import update_db
    update_db()


@celery_app.task
def update_website_task() -> None:
    from app.data.globals import website_options
    from app.data.processing.core import update_db
    from app.twitter import tweet_current_status
    update_db()
    if website_options.boating_season:
        tweet_current_status()


@celery_app.task
def send_database_exports_task() -> None:
    from app.data.processing.core import send_database_exports
    send_database_exports()


# Some IDEs have a hard time getting type annotations for decorated objects.
# Down here, we define the types for the tasks to help the IDE.
live_hobolink_data_task: WithAppContextTask
live_usgs_data_task: WithAppContextTask
combine_data_task: WithAppContextTask
clear_cache_task: WithAppContextTask
prediction_task: WithAppContextTask
update_db_task: WithAppContextTask
update_website_task: WithAppContextTask
send_database_exports_task: WithAppContextTask
