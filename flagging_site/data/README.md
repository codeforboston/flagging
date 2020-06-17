# Content of data

- `/_store`: contains pickle files used to test webpage offline using data provided already from usgus.pickle and hobolink.pickle
- `__init__.py`: required to treat directory as a package
- `database.py`: file handling database connection
- `hobolink.py`: retrieve hobolink by requesting a response and parsing data from hobolink 
- `keys.py`: handles access and tokens for hoblink and usgs API. Vault.zip provides keys.yml that provides the credentials
- `model.py`: outputs table model by processing usgs and hobolink data 
- `task_queue`: set up task queue 
- `usgs.py`: retrieve hobolink by requesting a response and parsing data from usgs
