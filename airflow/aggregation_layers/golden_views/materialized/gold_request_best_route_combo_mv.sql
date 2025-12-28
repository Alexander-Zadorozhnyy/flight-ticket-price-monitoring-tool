WITH route_min_price AS (
    SELECT
        request_id,
        route_id,
        route_type,
        MIN(amount) AS route_min_price,
        currency
    FROM silver_flight_prices_enriched
    GROUP BY request_id, route_id, route_type, currency
),

route_pairs AS (
    SELECT
        r1.request_id,
        r1.route_id AS to_route_id,
        r2.route_id AS return_route_id,
        (r1.route_min_price + r2.route_min_price) AS total_price,
        r1.currency
    FROM route_min_price r1
    JOIN route_min_price r2
        ON r1.request_id = r2.request_id
       AND r1.route_type = 'to_destination'
       AND r2.route_type = 'return'
),

one_way AS (
    SELECT
        request_id,
        route_id AS to_route_id,
        NULL::int AS return_route_id,
        route_min_price AS total_price,
        currency
    FROM route_min_price
    WHERE route_type = 'to_destination'
)

SELECT DISTINCT ON (request_id)
    request_id,
    to_route_id,
    return_route_id,
    total_price,
    currency
FROM (
    SELECT * FROM route_pairs
    UNION ALL
    SELECT * FROM one_way
) x
ORDER BY request_id, total_price;

CREATE UNIQUE INDEX IF NOT EXISTS ux_gold_best_combo
ON gold_request_best_route_combo_mv (request_id);