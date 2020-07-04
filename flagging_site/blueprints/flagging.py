import pandas as pd
from flask import Blueprint
from flask import render_template
from flagging_site.data.hobolink import get_hobolink_data
from flagging_site.data.usgs import get_usgs_data
from flagging_site.data.model import process_data
from flagging_site.data.model import reach_2_model
from flagging_site.data.model import reach_3_model
from flagging_site.data.model import reach_4_model
from flagging_site.data.model import reach_5_model
from flask_restful import Resource, Api

bp = Blueprint('flagging', __name__)

@bp.route('/')
def index() -> str:
    """
    Retrieves data from hobolink and usgs and processes data, then displays data 
    on `index_model.html`     

    returns: render model on index.html
    """
    df_hobolink = get_hobolink_data('code_for_boston_export_21d')
    df_usgs = get_usgs_data()
    df = process_data(df_hobolink, df_usgs)
    flags = {
        2: reach_2_model(df, rows=1)['r2_safe'].iloc[0],
        3: reach_3_model(df, rows=1)['r3_safe'].iloc[0],
        4: reach_4_model(df, rows=1)['r4_safe'].iloc[0],
        5: reach_5_model(df, rows=1)['r5_safe'].iloc[0]
    }
    return render_template('index.html', flags=flags)

api = Api(bp)

def add_to_dict(models, df, reach) -> None:
    """
    Iterates through dataframe from model output, adds to model dict where
    key equals column name, value equals column values as list type

    args:
        models: dictionary
        df: pd.DataFrame
        reach:int

    returns: None
        """
    model = {}
    # converts time column to type string because of conversion to json error
    df.time = df.time.astype(str)
    for (name, col) in df.iteritems():
        model[name] = col.tolist()

    models['model ' + str(reach)] = model

class ReachApi(Resource):
    def output_model(self) -> dict:
        """
        Class method that retrieves data from hobolink and usgs and processes data, then creates json-like dictionary
            structure for model output

        returns: json-like dictionary
        """
        df_hobolink = get_hobolink_data('code_for_boston_export_21d')
        df_usgs = get_usgs_data()
        df = process_data(df_hobolink, df_usgs)
        dfs = [
            reach_2_model(df),
            reach_3_model(df),
            reach_4_model(df),
            reach_5_model(df)
        ]
        main = {}
        models = {}
        # adds metadata
        main['version'] = '2020'
        main['time returned'] = 'last night'


        for counter, df in enumerate(dfs):
            add_to_dict(models, df, counter + 2)
        # adds models dict to main dict
        main['models'] = models

        return main

    def get(self):
        return self.output_model()

api.add_resource(ReachApi, '/output_model')