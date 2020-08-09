-- This query returns up to 48 hours of the latest data

SELECT *
FROM model_outputs
WHERE time BETWEEN 
	(SELECT MAX(time) - interval '47 hours' FROM model_outputs)
	AND 
	(SELECT MAX(time) FROM model_outputs)