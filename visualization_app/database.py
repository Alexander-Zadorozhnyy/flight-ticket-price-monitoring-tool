# database.py
import os
import pandas as pd
from sqlalchemy import create_engine


class FlightDataVisualizer:
    def __init__(self):
        self.engine = create_engine(
            f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('DB_NAME')}?sslmode=disable"
        )

    def fetch_best_flights(self):
        """Fetch data from gold_request_best_flights_mv"""
        query = """
        SELECT * FROM gold_request_best_flights_mv 
        ORDER BY found_at DESC 
        LIMIT 1000
        """
        return pd.read_sql(query, self.engine)

    def fetch_best_combos(self):
        """Fetch data from gold_request_best_route_combo_mv"""
        query = "SELECT * FROM gold_request_best_route_combo_mv"
        return pd.read_sql(query, self.engine)

    def fetch_price_timeseries(self, request_id=None):
        """Fetch data from gold_request_price_timeseries_mv"""
        query = "SELECT * FROM gold_request_price_timeseries_mv"
        if request_id:
            query += f" WHERE request_id = {request_id}"
        query += " ORDER BY price_date"
        return pd.read_sql(query, self.engine)

    def fetch_search_sessions(self, days_back=30):
        """Fetch search session data including quality metrics"""
        query = f"""
        SELECT 
            id,
            search_at,
            site_aggregator,
            status,
            quality
        FROM search_sessions 
        WHERE search_at > NOW() - INTERVAL '{days_back} days'
        ORDER BY search_at DESC
        """
        return pd.read_sql(query, self.engine)

    def fetch_session_quality_metrics(self):
        """Fetch aggregated quality metrics"""
        query = """
        WITH quality_data AS (
            SELECT 
                site_aggregator,
                DATE(search_at) as search_date,
                status,
                (quality->>'overall_quality') as overall_quality,
                (quality->'merged_quality'->>'overall_completeness')::float as overall_completeness,
                (quality->'merged_quality'->>'valid_flights')::int as valid_flights,
                (quality->'merged_quality'->>'invalid_flights')::int as invalid_flights,
                (quality->'merged_quality'->>'total_flights')::int as total_flights,
                (quality->'route_statistics'->>'avg_completeness_per_route')::float as avg_completeness,
                (quality->'quality_ratios'->>'valid_flights_ratio')::float as valid_ratio
            FROM search_sessions
            WHERE quality IS NOT NULL
        )
        SELECT * FROM quality_data
        """
        return pd.read_sql(query, self.engine)
