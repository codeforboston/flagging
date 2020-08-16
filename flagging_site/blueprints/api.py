from typing import Optional
from typing import List

import pandas as pd
from flask import Blueprint
from flask import render_template
from flask import request
from flask_restful import Api
from flask_restful import Resource
from flask import current_app

from ..data.hobolink import get_live_hobolink_data
from ..data.usgs import get_live_usgs_data
from ..data.model import process_data
from ..data.model import reach_2_model
from ..data.model import reach_3_model
from ..data.model import reach_4_model
from ..data.model import reach_5_model

from flasgger import swag_from

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


def model_api(reaches: Optional[List[int]], hours: Optional[int]) -> dict:
    """
    Class method that retrieves data from hobolink and usgs and processes
    data, then creates json-like dictionary structure for model output.

    returns: json-like dictionary
    """
    # Set defaults
    if reaches is None:
        reaches = [2, 3, 4, 5]
    if hours is None:
        hours = 24

    # `hours` must be between 1 and `API_MAX_HOURS`
    if hours > current_app.config['API_MAX_HOURS']:
        hours = current_app.config['API_MAX_HOURS']
    elif hours < 1:
        hours = 1

    df = get_data()

    dfs = {
        2: reach_2_model,
        3: reach_3_model,
        4: reach_4_model,
        5: reach_5_model
    }

    main = {}
    models = {}

    # adds metadata
    main['version'] = '2020'
    main['time_returned'] = str(pd.to_datetime('today'))

    for reach, model_func in dfs.items():
        if reach in reaches:
            _df = model_func(df, hours)
            add_to_dict(models, _df, reach)

    # adds models dict to main dict
    main['models'] = models

    return main


class ReachesApi(Resource):
    @swag_from('reach_api.yml')
    def get(self):
        reaches = request.args.getlist('reach', type=int)
        hours = request.args.get('hours', type=int)
        return model_api(reaches, hours)


api.add_resource(ReachesApi, '/v1/model')
