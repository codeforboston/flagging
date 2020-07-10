class ReachApi(Resource):

    def model_api(self) -> dict:
        """
        Class method that retrieves data from hobolink and usgs and processes
        data, then creates json-like dictionary structure for model output.

        returns: json-like dictionary
        """
        df = get_data()

        dfs = {
            2: reach_2_model(df),
            3: reach_3_model(df),
            4: reach_4_model(df),
            5: reach_5_model(df)
        }

        main = {}
        models = {}

        # adds metadata
        main['version'] = '2020'
        main['time_returned'] = str(pd.to_datetime('today'))

        for reach, df in dfs.items():
            add_to_dict(models, df, reach)

        # adds models dict to main dict
        main['models'] = models

        return main

    def get(self):
        return self.model_api()


api.add_resource(ReachApi, '/api/v1/model')