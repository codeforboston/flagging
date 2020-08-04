-- This query returns the latest values for the model.

SELECT *
FROM model_outputs
WHERE time = (SELECT MAX(time) FROM model_outputs);
