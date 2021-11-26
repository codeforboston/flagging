"""This file tests that the schema of the API is valid. The schemas are defined
in the YAML files, and they in turn define how the API is supposed to work.
"""
import pytest
import schemathesis

from app.data import Boathouse


@pytest.fixture
def schema_fixture(app):
    schema = schemathesis.from_wsgi('/api/flagging_api.json', app)
    return schema


schema = schemathesis.from_pytest_fixture('schema_fixture')


# Skip the model input data endpoint for test purposes.
# We do not plan on maintaining this schema.
# The input to `endpoint=` removes the model_input_data from the schema:

@pytest.mark.filterwarnings("ignore:^.*'subtests' fixture.*$")
@schema.parametrize(endpoint='^(?!/api/v1/model_input_data$).*$')
def test_api_schema(case):
    """Test the API against the OpenAPI specification."""
    response = case.call_wsgi()
    case.validate_response(response)


def test_manual_override(client, db_session, cache):
    """Test to see that manual overrides show up properly in the REST API.
    Newton Yacht Club is used as an example. It starts out not overridden by
    default. Then it is overridden, the cache is cleared, and we test that the
    API is reporting it.
    """

    def _get_yacht_club():
        res = client.get('/api/v1/boathouses').json
        f = lambda x: x['boathouse'] == 'Newton Yacht Club'  # noqa
        yacht_club = list(filter(f, res['boathouses']))[0]
        return yacht_club

    # First test that it is not overridden.
    yacht_club = _get_yacht_club()
    assert not yacht_club['overridden']

    # Now update the entry in the database
    db_session \
        .query(Boathouse) \
        .filter(Boathouse.name == 'Newton Yacht Club') \
        .update({"overridden": True})
    db_session.commit()
    cache.clear()

    # Now make sure the API is showing that it's overridden.
    yacht_club = _get_yacht_club()
    assert yacht_club['overridden']
