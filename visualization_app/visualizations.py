# visualizations.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


class FlightVisualizations:
    @staticmethod
    def plot_best_prices_comparison(df):
        """Compare best prices by site aggregator"""
        fig = px.box(
            df,
            x="site_aggregator",
            y="best_price",
            color="route_type",
            title="Best Flight Prices by Aggregator and Route Type",
            labels={"best_price": "Price", "site_aggregator": "Aggregator"},
        )
        fig.update_layout(template="plotly_white")
        return fig

    @staticmethod
    def plot_price_timeseries(df, request_id=None):
        """Plot price trends over time"""
        if request_id:
            title = f"Price Time Series for Request {request_id}"
        else:
            title = "Flight Price Time Series"

        fig = px.line(
            df,
            x="price_date",
            y="min_price",
            color="route_type",
            title=title,
            labels={"min_price": "Minimum Price", "price_date": "Date"},
        )

        fig.update_layout(
            template="plotly_white",
            xaxis_title="Date",
            yaxis_title="Price",
            hovermode="x unified",
        )
        return fig

    @staticmethod
    def plot_combo_price_distribution(df):
        """Distribution of combined route prices"""
        fig = px.histogram(
            df,
            x="total_price",
            color="currency",
            nbins=50,
            title="Distribution of Combined Route Prices",
            labels={"total_price": "Total Price"},
        )

        fig.update_layout(template="plotly_white", showlegend=True, bargap=0.1)
        return fig

    @staticmethod
    def plot_aggregator_performance(df):
        """Visualize which aggregators find the best prices"""
        # Aggregate data
        aggregator_stats = (
            df.groupby(["site_aggregator", "route_type"])
            .agg({"best_price": ["mean", "min", "count"]})
            .round(2)
            .reset_index()
        )

        aggregator_stats.columns = [
            "site_aggregator",
            "route_type",
            "mean_price",
            "min_price",
            "count",
        ]

        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=(
                "Average Prices by Aggregator",
                "Minimum Prices by Aggregator",
            ),
        )

        # Plot 1: Mean prices
        for route_type in aggregator_stats["route_type"].unique():
            subset = aggregator_stats[aggregator_stats["route_type"] == route_type]
            fig.add_trace(
                go.Bar(
                    x=subset["site_aggregator"],
                    y=subset["mean_price"],
                    name=f"{route_type} (Avg)",
                    text=subset["mean_price"],
                    textposition="auto",
                ),
                row=1,
                col=1,
            )

        # Plot 2: Min prices
        for route_type in aggregator_stats["route_type"].unique():
            subset = aggregator_stats[aggregator_stats["route_type"] == route_type]
            fig.add_trace(
                go.Bar(
                    x=subset["site_aggregator"],
                    y=subset["min_price"],
                    name=f"{route_type} (Min)",
                    text=subset["min_price"],
                    textposition="auto",
                ),
                row=2,
                col=1,
            )

        fig.update_layout(
            template="plotly_white", height=800, showlegend=True, barmode="group"
        )

        fig.update_xaxes(title_text="Aggregator", row=1, col=1)
        fig.update_xaxes(title_text="Aggregator", row=2, col=1)
        fig.update_yaxes(title_text="Average Price", row=1, col=1)
        fig.update_yaxes(title_text="Minimum Price", row=2, col=1)

        return fig

    @staticmethod
    def plot_price_heatmap(df):
        """Heatmap of prices by date and route type"""
        pivot_df = df.pivot_table(
            values="min_price", index="price_date", columns="route_type", aggfunc="mean"
        ).fillna(0)

        fig = px.imshow(
            pivot_df.T,
            title="Price Heatmap by Date and Route Type",
            labels=dict(x="Date", y="Route Type", color="Price"),
            color_continuous_scale="RdYlGn_r",
            aspect="auto",
        )

        fig.update_layout(
            template="plotly_white", xaxis_title="Date", yaxis_title="Route Type"
        )
        return fig
