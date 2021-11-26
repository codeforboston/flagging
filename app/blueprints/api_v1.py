import warnings
from typing import Any
from typing import Dict
from typing import List

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

from ..data.globals import website_options
from app.data.processing.predictive_models import latest_model_outputs
from app.data.processing.predictive_models import MODEL_VERSION
from ..data import Boathouse
from ..data.database import execute_sql
from ..data.database import cache
from ..data.database import get_current_time

bp = Blueprint('api', __name__, url_prefix='/api')


def model_api(reaches: List[int], hours: int) -> dict:
    """
    Class method that retrieves data from hobolink and usgs and processes
    data, then creates json-like dictionary structure for model output.

    returns: dict
    """

    # get model output data from database
    df = latest_model_outputs(hours)

    def _slice_df_by_reach(r: int) -> Dict[str, Any]:
        return (
            df
            .loc[df['reach_id'] == r, :]
            .drop(columns=['reach_id'])
            .to_dict(orient='records')
        )

    return {
        'model_version': MODEL_VERSION,
        'time_returned': get_current_time(),
        # For some reason this casts to int when not wrapped in `bool()`:
        'is_boating_season': website_options.boating_season,
        'model_outputs': [
            {
                'predictions': _slice_df_by_reach(reach),
                'reach': reach
            }
            for reach in reaches
        ]
    }


# ========================================
# The REST API endpoints are defined below
# ========================================


@bp.route('/v1/model')
@cache.cached(query_string=True)
@swag_from('openapi/predictive_model.yml')
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
@cache.cached()
@swag_from('openapi/boathouse.yml')
def boathouses_api():
    """Returns JSON of the boathouses."""
    return jsonify(boathouses=Boathouse.all_boathouses_dict())


@bp.route('/v1/model_input_data')
@cache.cached(query_string=True)
@swag_from('openapi/model_input_data.yml')
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
