from flagging_site.data.hobolink import get_hobolink_data
from datetime import datetime


def test_get_hobolink_data():
    df = get_hobolink_data('code_for_boston_export')
    last_timestamp = df.iloc[-1][0]
    assert (last_timestamp.minute - datetime.now().minute) < 30
