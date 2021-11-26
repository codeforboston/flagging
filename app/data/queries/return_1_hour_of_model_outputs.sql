SELECT *
FROM prediction
WHERE time = (SELECT MAX(time) FROM prediction);
