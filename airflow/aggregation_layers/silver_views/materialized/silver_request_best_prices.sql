SELECT
    req.id              AS request_id,
    r.route_type,
    MIN(fp.amount)      AS best_price,
    fp.currency
FROM requests req
JOIN routes r ON r.request_id = req.id
JOIN flights f ON f.route_id = r.id
JOIN flight_prices fp ON fp.flight_id = f.id
GROUP BY req.id, r.route_type, fp.currency;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_request_best_price
ON silver_request_best_prices (request_id, route_type, currency);