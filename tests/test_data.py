from flagging_site.data.hobolink import get_hobolink_data
from datetime import datetime
import pandas as pd

def test_get_hobolink_data():
    df = get_hobolink_data('code_for_boston_export')
    last_timestamp = df['time'].iloc[-1]
    time_difference = (datetime.now()-last_timestamp)
    assert time_difference < pd.Timedelta('30 minutes')

