"""
Synchronous processing functions. Designed to be simple-stupid, and not shy
about adding a little repetition and not worrying about async processing-- both
in service of simplifying the code for ease of maintenance.
"""
from enum import Enum
from functools import partial
from typing import Optional
from typing import Protocol

import pandas as pd
from flask import current_app

from app.data.database import db
from app.data.database import execute_sql
from app.data.database import get_current_time
from app.data.globals import cache
from app.data.models.prediction import Prediction
from app.data.processing.hobolink import HOBOLINK_DEFAULT_EXPORT_NAME
from app.data.processing.hobolink import HOBOLINK_ROWS_PER_HOUR
from app.data.processing.hobolink import get_live_hobolink_data
from app.data.processing.usgs import USGS_DEFAULT_DAYS_AGO
from app.data.processing.usgs import USGS_ROWS_PER_HOUR
from app.data.processing.usgs import get_live_usgs_data
from app.mail import ExportEmail
from app.mail import mail
from app.mail import mail_on_fail


def _write_to_db(
        df: pd.DataFrame,
        table_name: str,
        rows: Optional[int] = None
) -> None:
    """Takes a Pandas DataFrame, and writes it to the database."""
    if rows is not None:
        df = df.tail(rows)
    df.to_sql(
        table_name,
        con=db.engine,
        index=False,
        if_exists='replace'
    )


class ModelModule(Protocol):

    MODEL_YEAR: str

    def process_data(self, df_hobolink: pd.DataFrame, df_usgs: pd.DataFrame) -> pd.DataFrame:
        ...

    def all_models(self, df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
        ...


class ModelVersion(str, Enum):
    v1 = "v1"
    v2 = "v2"
    v3 = "v3"

    def get_module(self) -> ModelModule:
        if self == self.__class__.v1:
            from app.data.processing.predictive_models import v1
            return v1
        elif self == self.__class__.v2:
            from app.data.processing.predictive_models import v2
            return v2
        elif self == self.__class__.v3:
            from app.data.processing.predictive_models import v3
            return v3
        else:
            raise ValueError(f"Unclear what happened; {self} not supported")


DEFAULT_MODEL_VERSION = ModelVersion.v1


@mail_on_fail
def _combine_job(
        days_ago: int = USGS_DEFAULT_DAYS_AGO,
        export_name: str = HOBOLINK_DEFAULT_EXPORT_NAME,
        model_version: ModelVersion = DEFAULT_MODEL_VERSION
) -> pd.DataFrame:
    mod = model_version.get_module()
    df_usgs = get_live_usgs_data(days_ago=days_ago)
    df_hobolink = get_live_hobolink_data(export_name=export_name)
    df_combined = mod.process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
    return df_combined


combine_v1_job = partial(_combine_job, model_version=ModelVersion.v1)
combine_v2_job = partial(_combine_job, model_version=ModelVersion.v2)
combine_v3_job = partial(_combine_job, model_version=ModelVersion.v3)


@mail_on_fail
def _predict_job(
        days_ago: int = USGS_DEFAULT_DAYS_AGO,
        export_name: str = HOBOLINK_DEFAULT_EXPORT_NAME,
        model_version: ModelVersion = DEFAULT_MODEL_VERSION
) -> pd.DataFrame:
    mod = model_version.get_module()
    df_usgs = get_live_usgs_data(days_ago=days_ago)
    df_hobolink = get_live_hobolink_data(export_name=export_name)
    df_combined = mod.process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
    df_predictions = mod.all_models(df_combined)
    return df_predictions


predict_v1_job = partial(_predict_job, model_version=ModelVersion.v1)
predict_v2_job = partial(_predict_job, model_version=ModelVersion.v2)
predict_v3_job = partial(_predict_job, model_version=ModelVersion.v3)


@mail_on_fail
def update_db() -> None:
    mod = DEFAULT_MODEL_VERSION.get_module()
    df_usgs = get_live_usgs_data()
    df_hobolink = get_live_hobolink_data()
    df_combined = mod.process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
    df_predictions = mod.all_models(df_combined)

    hours = current_app.config['STORAGE_HOURS']
    try:
        _write_to_db(df_usgs, 'usgs', rows=hours * USGS_ROWS_PER_HOUR)
        _write_to_db(df_hobolink, 'hobolink', rows=hours * HOBOLINK_ROWS_PER_HOUR)
        _write_to_db(df_combined, 'processed_data')
        _write_to_db(df_predictions, Prediction.__tablename__)
    finally:
        # Clear the cache every time we are dumping to the database.
        # the try -> finally makes sure this always runs, even if an error
        # occurs somewhere when updating.
        cache.clear()


@mail_on_fail
def send_database_exports() -> None:
    mod = DEFAULT_MODEL_VERSION.get_module()
    df_usgs = get_live_usgs_data(days_ago=90)
    df_hobolink = get_live_hobolink_data(export_name='code_for_boston_export_90d')
    df_combined = mod.process_data(df_hobolink=df_hobolink, df_usgs=df_usgs)
    df_predictions = mod.all_models(df_combined)
    df_override_history = execute_sql('select * from override_history;')

    todays_date = get_current_time().strftime('%Y_%m_%d')

    msg = ExportEmail()

    msg.attach_dataframe(df_usgs, f'{todays_date}-usgs.csv')
    msg.attach_dataframe(df_hobolink, f'{todays_date}-hobolink.csv')
    msg.attach_dataframe(df_combined, f'{todays_date}-combined.csv')
    msg.attach_dataframe(df_predictions, f'{todays_date}-prediction.csv')
    msg.attach_dataframe(
        df_override_history,
        f'{todays_date}-override-history.csv'
    )

    mail.send(msg)
