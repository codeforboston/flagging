import pandas as pd
import requests


# Get data and parse returned JSON
url = "http://localhost/api/v1/model"
res = requests.get(url).json()
records = [
    {"reach": reach["reach"], **row}
    for reach in res["model_outputs"]
    for row in reach["predictions"]
]

# Turn into Pandas DataFrame
df = pd.DataFrame(records)
print(df.head())
