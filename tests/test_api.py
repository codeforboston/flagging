from flask import current_app
from flagging_site.blueprints.api import model_api
from flagging_site.data.model import reach_2_model
from flagging_site.data.model import process_data
from flagging_site.data.usgs import get_live_usgs_data
from flagging_site.data.hobolink import get_live_hobolink_data

def test_model_output_api_schema(app):
    """test_model_output_api_schema() should test that the keys are a particular way and the
    values are of a particular type."""
    with app.app_context():
        schema = {
            'version': dict
            }
        res = model_api([3], 10)

        for key, value in res.items():
            assert isinstance(key, str)


def test_model_output_api_parameters(app):
    """test_model_output_api_parameters() should test that hours=10 returns 10 rows of data,
    that setting the reach returns only that reach."""
    with app.app_context():
        df = reach_2_model(process_data(df_usgs=get_live_usgs_data(), df_hobolink=get_live_hobolink_data('code_for_boston_export_21d')), 10)
        row_count = len(df)
        assert row_count == 10
        test_reach = model_api([3], 10)
        test_reach = list(test_reach.values())
        expected_reach = list(test_reach[2].items())[0][0]
        assert 'reach_3' == expected_reach


def test_max_hours(app):
    """Test that the API never returns more than the max number of hours."""
    with app.app_context():
        max_hours = current_app.config['API_MAX_HOURS']
        excess_hours = current_app.config['API_MAX_HOURS'] + 10
        rows_returned = len(model_api(None, excess_hours)['models']['reach_2']['time'])
        assert rows_returned == max_hours
