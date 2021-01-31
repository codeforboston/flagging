import warnings
from typing import List

import pandas as pd
from flask import Blueprint
from flask import request
from flask import current_app
from flask import jsonify
from flask import url_for
from flask import Flask
with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=DeprecationWarning)
    from flasgger import Swagger
    from flasgger import LazyString
    from flasgger import swag_from

from ..data.predictive_models import latest_model_outputs
from ..data.predictive_models import MODEL_VERSION
from ..data.boathouses import Boathouse
from ..data.database import execute_sql
from ..data.database import cache
from ..data.live_website_options import LiveWebsiteOptions


bp = Blueprint('api', __name__, url_prefix='/api')


def model_api(reaches: List[int], hours: int) -> dict:
    """
    Class method that retrieves data from hobolink and usgs and processes
    data, then creates json-like dictionary structure for model output.

    returns: dict
    """

    # get model output data from database
    df = latest_model_outputs(hours)
    return {
        'model_version': MODEL_VERSION,
        'time_returned': pd.to_datetime('today'),
        # For some reason this casts to int when not wrapped in `bool()`:
        'is_boating_season': LiveWebsiteOptions.is_boating_season(),
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
@cache.cached(timeout=21600, query_string=True)
@swag_from('predictive_model_api.yml')
def predictive_model_api():
    """Returns JSON of the predictive model outputs."""
    # Get the reaches from the query parameters.
    reaches = request.args.getlist('reach', type=int) or [2, 3, 4, 5]

    # Hours query parameter must be between 1 and API_MAX_HOURS.
    hours = request.args.get('hours', default=24, type=int)
    hours = min(hours, current_app.config['API_MAX_HOURS'])
    hours = max(hours, 1)

    # Get data
    data = model_api(reaches, hours)

    return jsonify(data)


@bp.route('/v1/boathouses')
@cache.cached(timeout=21600)
@swag_from('boathouses_api.yml')
def boathouses_api():
    """Returns JSON of the boathouses."""
    return jsonify(boathouses=Boathouse.all_boathouses_dict())


@bp.route('/v1/model_input_data')
@cache.cached(timeout=21600, query_string=True)
@swag_from('model_input_data_api.yml')
def model_input_data_api():
    """Returns records of the data used for the model."""
    # Parse inputs
    # Hours query parameter must be between 1 and API_MAX_HOURS.
    hours = request.args.get('hours', default=24, type=int)
    hours = min(hours, current_app.config['API_MAX_HOURS'])
    hours = max(hours, 1)

    df = execute_sql('''SELECT * FROM processed_data ORDER BY time''')

    model_input_data = df.tail(n=hours).to_dict(orient='records')

    return jsonify(model_input_data=model_input_data)


def init_swagger(app: Flask):
    """
    This function handles all the logic for adding Swagger automated
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
                'rule_filter': lambda rule: True,
                'model_filter': lambda tag: True,
            },
        ],
        'static_url_path': '/flasgger_static',
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
