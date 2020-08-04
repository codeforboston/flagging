-- This query returns 48 hours of data,
-- (unless the time interval in the data is less than 48 hours, 
-- in which case it will return data for all timestamps)

SELECT *
FROM model_outputs
WHERE time BETWEEN 
	(SELECT MAX(time) - interval '47 hours' FROM model_outputs)
	AND 
	(SELECT MAX(time) FROM model_outputs)