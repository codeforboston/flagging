"""This file tests that the schema of the API is valid. The schemas are defined
in the YAML files, and they in turn define how the API is supposed to work.
"""
import pytest
import schemathesis


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
def test_api(case):
    """Test the API against the OpenAPI specification."""
    response = case.call_wsgi()
    case.validate_response(response)
