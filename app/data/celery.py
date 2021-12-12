from typing import Tuple, List, Dict, Any, TypeVar, Union
from abc import ABCMeta

import pandas as pd
from celery import Task
from celery import Celery as _Celery
from celery import group
from celery.canvas import Signature
from celery.result import AsyncResult
from celery.signals import task_prerun
from celery.signals import task_postrun
from flask import Flask
from flask import current_app

from app.data.database import db
from app.data.processing.hobolink import DEFAULT_HOBOLINK_EXPORT_NAME
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.usgs import get_live_usgs_data
from app.data.processing.predictive_models import process_data
from app.data.processing.predictive_models import all_models
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


@task_prerun.connect()
def task_starting_handler(sender=None, task_id=None, **kwargs):
    print(f'Starting task {task_id!r} from {sender!r}')


@task_postrun.connect()
def task_finished_handler(sender=None, task_id=None, **kwargs):
    print(f'Finished task {task_id!r} from {sender!r}')


def init_celery(app: Flask):
    celery_app.flask_app = app
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )


@celery_app.task
@mail_on_fail
def live_hobolink_data_task(
        export_name: str = DEFAULT_HOBOLINK_EXPORT_NAME,
        write_to_db: bool = False
) -> RecordsType:
    df = get_live_hobolink_data(export_name=export_name)

    if write_to_db:
        num_rows_to_store = current_app.config['STORAGE_HOURS'] * 6
        df.tail(num_rows_to_store).to_sql(
            'hobolink',
            con=db.engine,
            index=False,
            if_exists='replace'
        )

    return df.to_dict(orient='records')


@celery_app.task
@mail_on_fail
def live_usgs_data_task(
        days_ago: int = 14,
        write_to_db: bool = False
) -> RecordsType:
    df = get_live_usgs_data(days_ago=days_ago)

    if write_to_db:
        num_rows_to_store = current_app.config['STORAGE_HOURS'] * 4
        df.tail(num_rows_to_store).to_sql(
            'usgs',
            con=db.engine,
            index=False,
            if_exists='replace'
        )

    return df.to_dict(orient='records')


@celery_app.task
@mail_on_fail
def combine_data_task(
        hobolink_and_usgs: Tuple[RecordsType, RecordsType],
        write_to_db: bool = False
) -> RecordsType:
    hobo, usgs = hobolink_and_usgs

    df = process_data(
        df_hobolink=pd.DataFrame(hobo),
        df_usgs=pd.DataFrame(usgs)
    )

    if write_to_db:
        df.to_sql(
            'processed_data',
            con=db.engine,
            index=False,
            if_exists='replace'
        )

    return df.to_dict(orient='records')


@celery_app.task
@mail_on_fail
def run_predictive_models_task(
        processed_data: RecordsType,
        write_to_db: bool = False,
) -> RecordsType:

    df = all_models(
        df=pd.DataFrame(processed_data)
    )

    if write_to_db:
        from app.data.models.prediction import Prediction
        df.to_sql(
            Prediction.__tablename__,
            con=db.engine,
            index=False,
            if_exists='replace'
        )

    return df.to_dict(orient='records')


@celery_app.task
@mail_on_fail
def clear_cache_task() -> None:
    from app.data.globals import cache
    # TODO: Make sure the way the cache clears doesn't impact the celery task
    #  queue!
    cache.clear()


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
    pipeline |= clear_cache_task.s()

    return pipeline


def build_email_pipeline(
        hobolink_kwargs: Dict[str, Any] = None,
        usgs_kwargs: Dict[str, Any] = None,
) -> Signature:
    if hobolink_kwargs is None:
        hobolink_kwargs = {}
    if usgs_kwargs is None:
        usgs_kwargs = {}

    pipeline = group((
        live_hobolink_data_task.s(**hobolink_kwargs),
        live_usgs_data_task.s(**usgs_kwargs)
    ))

    pipeline |= combine_data_task.s()
    pipeline |= run_predictive_models_task.s()

    return pipeline


def parse_pipeline_result_object(res: AsyncResult) -> Dict[str, AsyncResult]:
    tup = res.as_tuple()
    return {
        'prediction': res,
        'processed_data': AsyncResult(tup[0][1][0][0]),
        'hobolink': AsyncResult(tup[0][1][1][0][0][0]),
        'usgs': AsyncResult(tup[0][1][1][1][0][0]),
    }


live_hobolink_data_task: WithAppContextTask
live_usgs_data_task: WithAppContextTask
combine_data_task: WithAppContextTask
run_predictive_models_task: WithAppContextTask
