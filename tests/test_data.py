import requests


class TestData:
    def test_get_hobolink_data(self):
        data = {
            'query': 'code_for_boston_export',         #hard-coded this value in to make test work
            'authentication': get_keys()['hobolink']   #looked in keys.py to find this
                                                       # tried echoing envir vars, no luck
        }
        hobolink_url = 'http://webservice.hobolink.com/restv2/data/custom/file'
        res = requests.post(hobolink_url, json=data)
        assert res.status_code == 200

