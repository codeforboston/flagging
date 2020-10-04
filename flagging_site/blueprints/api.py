from typing import List

import pandas as pd
from flask import Blueprint
from flask import render_template
from flask import request
from flask import current_app
from flask import jsonify
from ..data.predictive_models import latest_model_outputs
from ..data.predictive_models import MODEL_VERSION
from ..data.database import get_boathouse_metadata_dict
from ..data.database import execute_sql

from flasgger import swag_from

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/', methods=['GET'])
def index() -> str:
    """Landing page for the API."""
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


def model_api(reaches: List[int], hours: int) -> dict:
    """
    Class method that retrieves data from hobolink and usgs and processes
    data, then creates json-like dictionary structure for model output.

    returns: json-like dictionary
    """
    # First step is to validate inputs

    # `hours` must be an integer between 1 and `API_MAX_HOURS`. Default is 24
    if hours > current_app.config['API_MAX_HOURS']:
        hours = current_app.config['API_MAX_HOURS']
    elif hours < 1:
        hours = 1
    # `reaches` must be a list of integers. Default is all the reaches.

    # get model output data from database
    df = latest_model_outputs(hours)
    return {
        'model_version': MODEL_VERSION,
        'time_returned': pd.to_datetime('today'),
        'model_outputs': [
            {
                'predictions': df.loc[
                    df['reach'] == int(reach), :
                ].drop(columns=['reach']).to_dict(orient='records'),
                'reach': reach
            }
            for reach in reaches
        ]
    }


# ========================================
# The REST API endpoints are defined below
# ========================================


@bp.route('/v1/model')
@swag_from('predictive_model_api.yml')
def predictive_model_api():
    """Returns JSON of the predictive model outputs."""
    reaches = request.args.getlist('reach', type=int) or [2, 3, 4, 5]
    hours = request.args.get('hours', type=int) or 24
    return jsonify(model_api(reaches, hours))


@bp.route('/v1/boathouses')
@swag_from('boathouses_api.yml')
def boathouses_api():
    """Returns JSON of the boathouses."""
    boathouse_metadata_dict = get_boathouse_metadata_dict()
    return jsonify(boathouse_metadata_dict)


@bp.route('/v1/model_input_data')
@swag_from('model_input_data_api.yml')
def model_input_data_api():
    """Returns records of the data used for the model."""
    df = execute_sql('''SELECT * FROM processed_data ORDER BY time''')

    # Parse the hours
    hours = request.args.get('hours', type=int) or 24
    if hours > current_app.config['API_MAX_HOURS']:
        hours = current_app.config['API_MAX_HOURS']
    elif hours < 1:
        hours = 1

    return jsonify({
        'model_input_data': df.tail(n=hours).to_dict(orient='records')
    })
