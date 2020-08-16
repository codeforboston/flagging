from flagging_site.blueprints.api import model_api
from flask import current_app


def test_max_hours(app):
    """Test that the API never returns more than the max number of hours."""
    with app.app_context():
        max_hours = current_app.config['API_MAX_HOURS']
        excess_hours = current_app.config['API_MAX_HOURS'] + 10
        rows_returned = len(model_api(None, excess_hours)['models']['reach_2']['time'])
        assert rows_returned == max_hours
