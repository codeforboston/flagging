import pandas as pd
from flask import Blueprint
from flask import render_template
from flagging_site.data.hobolink import get_hobolink_data
from flagging_site.data.usgs import get_usgs_data
from flagging_site.data.model import process_data
from flagging_site.data.model import reach_2_model
from flagging_site.data.model import reach_3_model
from flagging_site.data.model import reach_4_model
from flagging_site.data.model import reach_5_model
from flask_restful import Resource, Api

from flask import Blueprint

bp = Blueprint('api', __name__,url_prefix='/api')
api = Api(bp)

def get_data() -> pd.DataFrame:
    """Retrieves the data that gets plugged into the the model."""
    df_hobolink = get_hobolink_data('code_for_boston_export_21d')
    df_usgs = get_usgs_data()
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


def model_api(reach_param: list = None) -> dict:
    """
    Class method that retrieves data from hobolink and usgs and processes
    data, then creates json-like dictionary structure for model output.

    returns: json-like dictionary
    """
    reach_param = reach_param or [2,3,4,5]
    df = get_data()

    dfs = {
        2: reach_2_model(df),
        3: reach_3_model(df),
        4: reach_4_model(df),
        5: reach_5_model(df)
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

class ReachApi(Resource):
    def get(self,reach):
        reach_params = [reach]
        return model_api(reach_params)

class ReachesApi(Resource):
    def get(self):
        return model_api()

api.add_resource(ReachApi, '/v1/model/<int:reach>')

@bp.route('/', methods=['GET'])
def api_landing_page() -> str:
    return render_template('api/index.html')

api.add_resource(ReachesApi, '/v1/model')
