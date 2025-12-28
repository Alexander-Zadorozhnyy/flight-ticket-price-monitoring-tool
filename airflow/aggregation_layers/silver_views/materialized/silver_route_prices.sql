SELECT
    r.id                  AS route_id,
    r.departure,
    r.arrival,
    r.departure_date,
    COUNT(DISTINCT f.id)  AS flights_count,
    COUNT(DISTINCT CASE WHEN f.is_direct THEN f.id END) AS direct_flights_count,
    MIN(fp.amount)        AS min_price,
    AVG(fp.amount)        AS avg_price,
    MAX(fp.amount)        AS max_price,
    fp.currency
FROM routes r
JOIN flights f ON f.route_id = r.id
JOIN flight_prices fp ON fp.flight_id = f.id
GROUP BY
    r.id, r.departure, r.arrival, r.departure_date, fp.currency;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_route_prices
ON silver_route_prices (route_id, currency);