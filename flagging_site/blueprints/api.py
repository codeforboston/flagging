from typing import Optional
from typing import List

import pandas as pd
from flask import Blueprint
from flask import render_template
from flask import request
from flask_restful import Api
from flask_restful import Resource
from flask import current_app
from ..data.predictive_models import latest_model_outputs
from ..data.database import get_boathouse_metadata_dict

from flasgger import swag_from

bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(bp)


@bp.route('/', methods=['GET'])
def index() -> str:
    return render_template('api/index.html')


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

    # set default `hours` must be between 1 and `API_MAX_HOURS`
    if hours is None:
        hours = 24
    
    # `hours` must be between 1 and `API_MAX_HOURS`
    if hours > current_app.config['API_MAX_HOURS']:
        hours = current_app.config['API_MAX_HOURS']
    elif hours < 1:
        hours = 1

    # get model output data from database
    df = latest_model_outputs(hours)

    # converts time column to type string because of conversion to json error
    df['time'] = df['time'].astype(str)

    # set default `reaches`:  all reach values in the data
    if not reaches:
        reaches = df.reach.unique()
    
    # construct secondary dictionary from the file (tertiary dicts will be built along the way)
    sec_dict = {}
    for reach_num in reaches:
        tri_dict = {}
        for field in df.columns:
            tri_dict[field] = df[df['reach']==reach_num][field].tolist()
        sec_dict["model_"+str(reach_num)] = tri_dict

    # create return value (primary dictionary)
    prim_dict = { 
        "version" : "2020", 
        "time_returned":str( pd.to_datetime('today') ),
        "models": sec_dict
    }

    return prim_dict


class ReachesApi(Resource):
    @swag_from('reach_api.yml')
    def get(self):
        reaches = request.args.getlist('reach', type=int)
        hours = request.args.get('hours', type=int)
        return model_api(reaches, hours)


api.add_resource(ReachesApi, '/v1/model')


class BoathousesApi(Resource):
    @swag_from('boathouses_api.yml')
    def get(self):
        boathouse_metadata_dict = get_boathouse_metadata_dict()
        return boathouse_metadata_dict


api.add_resource(BoathousesApi, '/v1/boathouses')
