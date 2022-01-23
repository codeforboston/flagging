SELECT *
FROM prediction
WHERE time BETWEEN 
    (SELECT MAX(time) - interval '47 hours' FROM prediction)
    AND
    (SELECT MAX(time) FROM prediction);
