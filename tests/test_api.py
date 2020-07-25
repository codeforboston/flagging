from flagging_site.blueprints.api import model_api
from flagging_site.config import API_MAX_HOURS

def test_max_hours(app):
    with app.app_context():
        assert len(model_api(None,API_MAX_HOURS + 10)['models']['reach_2']['time']) == 48