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

from app.data.globals import website_options
from app.data.processing.predictive_models import MODEL_VERSION
from app.data.globals import boathouses
from app.data.globals import reaches
from app.data.globals import cache
from app.data.database import execute_sql
from app.data.database import get_current_time

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/v1/model')
@cache.cached(query_string=True)
@swag_from('openapi/predictive_model.yml')
def predictive_model_api():
    """Returns JSON of the predictive model outputs."""
    # Get the reaches from the query parameters.
    selected_reaches = request.args.getlist('reach', type=int) or [2, 3, 4, 5]

    # Hours query parameter must be between 1 and API_MAX_HOURS.
    selected_hours = request.args.get('hours', default=24, type=int)
    selected_hours = min(selected_hours, current_app.config['API_MAX_HOURS'])
    selected_hours = max(selected_hours, 1)

    return jsonify({
        'model_version': MODEL_VERSION,
        'time_returned': get_current_time(),
        'is_boating_season': website_options.boating_season,
        'model_outputs': [
            {
                'reach': r.id,
                'predictions': [
                    p.api_v1_to_dict()
                    for p in r.predictions_last_x_hours(x=selected_hours)
                ]
            }
            for r in filter(lambda _: _.id in selected_reaches, reaches)
        ]
    })


@bp.route('/v1/boathouses')
@cache.cached()
@swag_from('openapi/boathouse.yml')
def boathouses_api():
    """Returns JSON of the boathouses."""
    return jsonify(boathouses=[bh.api_v1_to_dict() for bh in boathouses])


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

    df = execute_sql('''SELECT * FROM processed_data ORDER BY time;''')

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
