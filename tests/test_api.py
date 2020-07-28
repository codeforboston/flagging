from flagging_site.blueprints.api import model_api
from flask import current_app

def test_max_hours(app):
    with app.app_context():
        assert len(model_api(None,current_app.config['API_MAX_HOURS'] + 10)['models']['reach_2']['time']) == 48

