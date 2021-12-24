from abc import ABCMeta
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar

import pandas as pd
from celery import Celery as _Celery
from celery import group
from celery import Task
from celery.canvas import Signature
from celery.result import AsyncResult
from celery.signals import task_postrun
from celery.signals import task_prerun
from celery.utils.log import get_task_logger
from flask import current_app
from flask import Flask

from app.data.database import db
from app.data.processing.hobolink import HOBOLINK_DEFAULT_EXPORT_NAME
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.predictive_models import all_models
from app.data.processing.predictive_models import process_data
from app.data.processing.usgs import get_live_usgs_data
from app.data.processing.core import combine_job
from app.data.processing.core import predict_job
from app.data.processing.core import update_db
from app.mail import mail_on_fail

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
logger = get_task_logger(__name__)


@task_prerun.connect()
def task_starting_handler(sender=None, task_id=None, **kwargs):
    logger.info(f'Starting task {task_id!r} from {sender!r}')


@task_postrun.connect()
def task_finished_handler(sender=None, task_id=None, **kwargs):
    logger.info(f'Finished task {task_id!r} from {sender!r}')


def init_celery(app: Flask):
    celery_app.flask_app = app
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )


@celery_app.task
def live_hobolink_data_task(*args, **kwargs) -> RecordsType:
    df = get_live_hobolink_data(*args, **kwargs)
    return df.to_dict(orient='records')


@celery_app.task
def live_usgs_data_task(*args, **kwargs) -> RecordsType:
    df = get_live_usgs_data(*args, **kwargs)
    return df.to_dict(orient='records')


@celery_app.task
def combine_data_task(*args, **kwargs) -> RecordsType:
    df = combine_job(*args, **kwargs)
    return df.to_dict(orient='records')


@celery_app.task
def predict_task(*args, **kwargs) -> RecordsType:
    df = predict_job(*args, **kwargs)
    return df.to_dict(orient='records')


@celery_app.task
def update_db_task(*args, **kwargs) -> None:
    update_db(*args, **kwargs)


def build_pipeline(
        write_to_db: bool = False,
        hobolink_kwargs: Dict[str, Any] = None,
        usgs_kwargs: Dict[str, Any] = None,
) -> Signature:
    if hobolink_kwargs is None:
        hobolink_kwargs = {}
    if usgs_kwargs is None:
        usgs_kwargs = {}

    pipeline = group((
        live_hobolink_data_task.s(write_to_db=write_to_db, **hobolink_kwargs),
        live_usgs_data_task.s(write_to_db=write_to_db, **usgs_kwargs)
    ))

    pipeline |= combine_data_task.s(write_to_db=write_to_db)
    pipeline |= run_predictive_models_task.s(write_to_db=write_to_db)
    pipeline |= clear_cache_task.si()

    return pipeline


# def build_email_pipeline(
#         hobolink_kwargs: Dict[str, Any] = None,
#         usgs_kwargs: Dict[str, Any] = None,
# ) -> Signature:
#     if hobolink_kwargs is None:
#         hobolink_kwargs = {}
#     if usgs_kwargs is None:
#         usgs_kwargs = {}
#
#     pipeline = group((
#         live_hobolink_data_task.s(**hobolink_kwargs),
#         live_usgs_data_task.s(**usgs_kwargs)
#     ))
#
#     pipeline |= combine_data_task.s()
#     pipeline |= run_predictive_models_task.s()
#
#     return pipeline


def parse_pipeline_result_object(res: AsyncResult) -> Dict[str, AsyncResult]:

    return {
        'prediction': res,
        'processed_data': res.parent,
        'hobolink': res.parent.results[0],
        'usgs': res.parent.results[1],
    }


live_hobolink_data_task: WithAppContextTask
live_usgs_data_task: WithAppContextTask
combine_data_task: WithAppContextTask
run_predictive_models_task: WithAppContextTask
clear_cache_task: WithAppContextTask
