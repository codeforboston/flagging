from typing import List

import pandas as pd
from flask import Blueprint
from flask import request
from flask import current_app
from flask import jsonify
from flask import url_for
from flask import Flask
from flasgger import Swagger
from flasgger import LazyString
from ..data.predictive_models import latest_model_outputs
from ..data.predictive_models import MODEL_VERSION
from ..data.database import get_boathouse_metadata_dict
from ..data.database import execute_sql
from ..data.live_website_options import is_boating_season

from flasgger import swag_from

bp = Blueprint('api', __name__, url_prefix='/api')


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
        'is_boating_season': is_boating_season(),
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
    reaches = request.args.getlist('reach', default=[2, 3, 4, 5], type=int)
    hours = request.args.get('hours', default=24, type=int)
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
    hours = request.args.get('hours', default=24, type=int)
    if hours > current_app.config['API_MAX_HOURS']:
        hours = current_app.config['API_MAX_HOURS']
    elif hours < 1:
        hours = 1

    return jsonify({
        'model_input_data': df.tail(n=hours).to_dict(orient='records')
    })


def init_swagger(app: Flask):
    """This function handles all the logic for adding Swagger automated
    documentation to the application instance.

    Args:
        app: A Flask application instance.
    """
    swagger_config = {
        'headers': [],
        'specs': [
            {
                'endpoint': 'flagging_api',
                'route': '/api/flagging_api.json',
                'rule_filter': lambda rule: True,  # all in
                'model_filter': lambda tag: True,  # all in
            },
        ],
        'static_url_path': '/flasgger_static',
        # 'static_folder': '/static/flasgger',
        'swagger_ui': True,
        'specs_route': '/api/docs'
    }
    template = {
        'info': {
            'title': 'CRWA Public Flagging API',
            'description':
                "API for the Charles River Watershed Association's predictive "
                'models, and the data used for those models.',
            'contact': {
                'x-responsibleOrganization': 'Charles River Watershed Association',
                'x-responsibleDeveloper': 'Code for Boston',
            },
            'version': '1.0',
        }
    }
    app.config['SWAGGER'] = {
        'uiversion': 3,
        'favicon': LazyString(
            lambda: url_for('static', filename='favicon/favicon.ico'))
    }

    Swagger(app, config=swagger_config, template=template)
