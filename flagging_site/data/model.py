"""
This file contains all the logic for modeling. The model takes data from the SQL
backend, do some calculations on that data, and then output model results.

The model should be an emulation of the model on the PHP website, although we
will have to put some work into making the model "Pythonic." We also may want to
store the model's coefficients in a yaml file, and then load those coefficients
so that CRWA can fit the model on new data whenever they want and simply update
a plain text file without having to touch the code, but that's a bit of a longer
term goal.
"""