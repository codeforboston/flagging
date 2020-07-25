import pandas as pd
from flask import Blueprint
from flask import render_template
from flask import request
from flask_restful import Api
from flask_restful import Resource

from ..data.hobolink import get_live_hobolink_data
from ..data.usgs import get_live_usgs_data
from ..data.model import process_data
from ..data.model import reach_2_model
from ..data.model import reach_3_model
from ..data.model import reach_4_model
from ..data.model import reach_5_model
from flagging_site.config import API_MAX_HOURS


bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(bp)


@bp.route('/', methods=['GET'])
def index() -> str:
    return render_template('api/index.html')


def get_data() -> pd.DataFrame:
    """Retrieves the data that gets plugged into the the model."""
    df_hobolink = get_live_hobolink_data('code_for_boston_export_21d')
    df_usgs = get_live_usgs_data()
    df = process_data(df_hobolink, df_usgs)
    return df


def add_to_dict(models, df, reach) -> None:
    """
    Iterates through dataframe from model output, adds to model dict where
    key equals column name, value equals column values as list type

    args:
        models: dictionary
        df: pd.DataFrame
        reach:int

    returns: None
        """
    # converts time column to type string because of conversion to json error
    df['time'] = df['time'].astype(str)
    models[f'reach_{reach}'] = df.to_dict(orient='list')


def model_api(reach_param: list, hour: str) -> dict:
    """
    Class method that retrieves data from hobolink and usgs and processes
    data, then creates json-like dictionary structure for model output.

    returns: json-like dictionary
    """
    if reach_param:
        reach_param = list(map(int, reach_param))

    reach_param = reach_param or [2, 3, 4, 5]

    hour = int(hour)

    if hour > API_MAX_HOURS:
        hour = API_MAX_HOURS
    elif hour < 1:
        hour = 1

    df = get_data()

    dfs = {
        2: reach_2_model(df, hour),
        3: reach_3_model(df, hour),
        4: reach_4_model(df, hour),
        5: reach_5_model(df, hour)
    }

    main = {}
    models = {}

    # adds metadata
    main['version'] = '2020'
    main['time_returned'] = str(pd.to_datetime('today'))

    for reach, df in dfs.items():
        if reach in reach_param:
            add_to_dict(models, df, reach)

    # adds models dict to main dict
    main['models'] = models

    return main


class ReachesApi(Resource):
    def get(self):
        reach = request.args.getlist('reach', None)
        hour = request.args.get('hour', API_MAX_HOURS)
        return model_api(reach,hour)


api.add_resource(ReachesApi, '/v1/model')
