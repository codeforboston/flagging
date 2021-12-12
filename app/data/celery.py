from typing import Tuple, List, Dict, Any, TypeVar, Union
from abc import ABCMeta

import pandas as pd
from celery import Task
from celery import Celery as _Celery
from celery import group
from celery.canvas import Signature
from flask import Flask
from flask import current_app
from app.data.database import db

from app.data.processing.hobolink import DEFAULT_HOBOLINK_EXPORT_NAME
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.usgs import get_live_usgs_data
from app.data.processing.predictive_models import process_data
from app.data.processing.predictive_models import all_models


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


def init_celery(app: Flask):
    celery_app.flask_app = app
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND']
    )


@celery_app.task
def live_hobolink_data_task(
        export_name: str = DEFAULT_HOBOLINK_EXPORT_NAME,
        write_to_db: bool = False
) -> RecordsType:
    print('getting hobolink data')
    df = get_live_hobolink_data(export_name=export_name)

    if write_to_db:
        print('writing hobolink to database')
        num_rows_to_store = current_app.config['STORAGE_HOURS'] * 6
        df.tail(num_rows_to_store).to_sql(
            'hobolink',
            con=db.engine,
            index=False,
            if_exists='replace'
        )

    return df.to_dict(orient='records')


@celery_app.task
def live_usgs_data_task(
        days_ago: int = 14,
        write_to_db: bool = False
) -> RecordsType:
    print('getting usgs data')
    df = get_live_usgs_data(days_ago=days_ago)

    if write_to_db:
        print('writing usgs to database')
        num_rows_to_store = current_app.config['STORAGE_HOURS'] * 4
        df.tail(num_rows_to_store).to_sql(
            'usgs',
            con=db.engine,
            index=False,
            if_exists='replace'
        )

    return df.to_dict(orient='records')


@celery_app.task
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
        print('writing processed_data to database')
        df.to_sql(
            'processed_data',
            con=db.engine,
            index=False,
            if_exists='replace'
        )

    return df.to_dict(orient='records')


@celery_app.task
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

    return pipeline


live_hobolink_data_task: WithAppContextTask
live_usgs_data_task: WithAppContextTask
combine_data_task: WithAppContextTask
run_predictive_models_task: WithAppContextTask
