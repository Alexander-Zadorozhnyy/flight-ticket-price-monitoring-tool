# quality_visualizations.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import json


class QualityVisualizations:
    @staticmethod
    def parse_quality_json(df):
        """Parse quality JSON and extract key metrics"""
        metrics = []

        for idx, row in df.iterrows():
            if row["quality"] is None:
                continue

            try:
                quality_data = (
                    row["quality"]
                    if isinstance(row["quality"], dict)
                    else json.loads(row["quality"])
                )

                metrics.append(
                    {
                        "session_id": row["id"],
                        "search_at": row["search_at"],
                        "site_aggregator": row["site_aggregator"],
                        "status": row["status"],
                        "overall_quality": quality_data.get("merged_quality", {}).get(
                            "overall_quality", "unknown"
                        ),
                        "overall_completeness": float(
                            quality_data.get("merged_quality", {}).get(
                                "overall_completeness", 0
                            )
                        ),
                        "total_routes": int(quality_data.get("total_routes", 0)),
                        "total_flights": int(
                            quality_data.get("merged_quality", {}).get(
                                "total_flights", 0
                            )
                        ),
                        "valid_flights": int(
                            quality_data.get("merged_quality", {}).get(
                                "valid_flights", 0
                            )
                        ),
                        "invalid_flights": int(
                            quality_data.get("merged_quality", {}).get(
                                "invalid_flights", 0
                            )
                        ),
                        "valid_ratio": float(
                            quality_data.get("quality_ratios", {}).get(
                                "valid_flights_ratio", 0
                            )
                        ),
                        "completeness_ratio": float(
                            quality_data.get("quality_ratios", {}).get(
                                "completeness_ratio", 0
                            )
                        ),
                        "avg_completeness": float(
                            quality_data.get("route_statistics", {}).get(
                                "avg_completeness_per_route", 0
                            )
                        ),
                        "total_warnings": int(
                            quality_data.get("field_issues", {}).get(
                                "total_warnings", 0
                            )
                        ),
                        "top_warning": next(
                            iter(
                                quality_data.get("field_issues", {}).get(
                                    "top_warnings", {}
                                )
                            ),
                            None,
                        )
                        if quality_data.get("field_issues", {}).get("top_warnings")
                        else None,
                    }
                )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                continue

        return pd.DataFrame(metrics)

    @staticmethod
    def plot_quality_trends(df):
        """Plot quality metrics trends over time"""
        if df.empty:
            return px.line(title="No quality data available")

        df["search_date"] = pd.to_datetime(df["search_at"]).dt.date

        # Group by date and aggregator
        daily_stats = (
            df.groupby(["search_date", "site_aggregator"])
            .agg(
                {
                    "overall_completeness": "mean",
                    "valid_ratio": "mean",
                    "session_id": "count",
                }
            )
            .reset_index()
        )

        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=(
                "Average Completeness Over Time",
                "Valid Flight Ratio Over Time",
            ),
            vertical_spacing=0.15,
        )

        for aggregator in df["site_aggregator"].unique():
            subset = daily_stats[daily_stats["site_aggregator"] == aggregator]

            fig.add_trace(
                go.Scatter(
                    x=subset["search_date"],
                    y=subset["overall_completeness"],
                    mode="lines+markers",
                    name=f"{aggregator} - Completeness",
                    line=dict(width=2),
                    marker=dict(size=8),
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=subset["search_date"],
                    y=subset["valid_ratio"],
                    mode="lines+markers",
                    name=f"{aggregator} - Valid Ratio",
                    line=dict(width=2, dash="dot"),
                    marker=dict(size=8),
                ),
                row=2,
                col=1,
            )

        fig.update_layout(
            template="plotly_white", height=700, showlegend=True, hovermode="x unified"
        )

        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Completeness Score", row=1, col=1, range=[0, 1])
        fig.update_yaxes(title_text="Valid Flight Ratio", row=2, col=1, range=[0, 1])

        return fig

    @staticmethod
    def plot_quality_distribution(df):
        """Plot distribution of quality scores"""
        if df.empty:
            return px.bar(title="No quality data available")

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=(
                "Overall Quality Distribution",
                "Completeness Score Distribution",
            ),
            specs=[[{"type": "pie"}, {"type": "histogram"}]],
        )

        # Pie chart for overall quality
        quality_counts = df["overall_quality"].value_counts().reset_index()
        quality_counts.columns = ["quality", "count"]

        fig.add_trace(
            go.Pie(
                labels=quality_counts["quality"],
                values=quality_counts["count"],
                hole=0.4,
                name="Quality Distribution",
                textinfo="label+percent",
                marker=dict(colors=px.colors.qualitative.Set3),
            ),
            row=1,
            col=1,
        )

        # Histogram for completeness
        fig.add_trace(
            go.Histogram(
                x=df["overall_completeness"],
                nbinsx=20,
                name="Completeness Distribution",
                marker_color="lightblue",
                opacity=0.7,
            ),
            row=1,
            col=2,
        )

        fig.update_layout(template="plotly_white", height=500, showlegend=False)

        fig.update_xaxes(title_text="Completeness Score", row=1, col=2, range=[0, 1])
        fig.update_yaxes(title_text="Count", row=1, col=2)

        return fig

    @staticmethod
    def plot_aggregator_quality_comparison(df):
        """Compare quality metrics across aggregators"""
        if df.empty:
            return px.bar(title="No quality data available")

        agg_stats = (
            df.groupby("site_aggregator")
            .agg(
                {
                    "overall_completeness": ["mean", "std", "count"],
                    "valid_ratio": "mean",
                    "avg_completeness": "mean",
                    "total_warnings": "mean",
                }
            )
            .round(3)
            .reset_index()
        )

        agg_stats.columns = [
            "site_aggregator",
            "mean_completeness",
            "std_completeness",
            "session_count",
            "mean_valid_ratio",
            "mean_avg_completeness",
            "mean_warnings",
        ]

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Mean Completeness by Aggregator",
                "Valid Flight Ratio",
                "Average Warnings per Session",
                "Session Count",
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "bar"}],
            ],
        )

        # Mean Completeness
        fig.add_trace(
            go.Bar(
                x=agg_stats["site_aggregator"],
                y=agg_stats["mean_completeness"],
                name="Mean Completeness",
                text=agg_stats["mean_completeness"].round(2),
                textposition="auto",
                marker_color="lightseagreen",
                error_y=dict(
                    type="data", array=agg_stats["std_completeness"], visible=True
                ),
            ),
            row=1,
            col=1,
        )

        # Valid Ratio
        fig.add_trace(
            go.Bar(
                x=agg_stats["site_aggregator"],
                y=agg_stats["mean_valid_ratio"],
                name="Valid Flight Ratio",
                text=agg_stats["mean_valid_ratio"].round(2),
                textposition="auto",
                marker_color="lightcoral",
            ),
            row=1,
            col=2,
        )

        # Warnings
        fig.add_trace(
            go.Bar(
                x=agg_stats["site_aggregator"],
                y=agg_stats["mean_warnings"],
                name="Avg Warnings",
                text=agg_stats["mean_warnings"].round(0),
                textposition="auto",
                marker_color="goldenrod",
            ),
            row=2,
            col=1,
        )

        # Session Count
        fig.add_trace(
            go.Bar(
                x=agg_stats["site_aggregator"],
                y=agg_stats["session_count"],
                name="Session Count",
                text=agg_stats["session_count"],
                textposition="auto",
                marker_color="mediumpurple",
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            template="plotly_white",
            height=700,
            showlegend=False,
            title_text="Aggregator Quality Comparison",
        )

        fig.update_yaxes(title_text="Score", row=1, col=1, range=[0, 1])
        fig.update_yaxes(title_text="Ratio", row=1, col=2, range=[0, 1])
        fig.update_yaxes(title_text="Warnings", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=2)

        return fig

    @staticmethod
    def plot_warnings_analysis(df):
        """Analyze warning patterns"""
        if df.empty:
            return px.bar(title="No quality data available")

        # Extract top warnings
        warnings_data = []
        for _, row in df.iterrows():
            if row["top_warning"]:
                warnings_data.append(
                    {
                        "aggregator": row["site_aggregator"],
                        "warning": row["top_warning"],
                        "count": row["total_warnings"],
                    }
                )

        if not warnings_data:
            return px.bar(title="No warning data available")

        warnings_df = pd.DataFrame(warnings_data)

        # Group by warning type
        warning_summary = (
            warnings_df.groupby(["warning", "aggregator"])
            .agg({"count": "sum"})
            .reset_index()
        )

        # Truncate long warning messages for display
        warning_summary["warning_short"] = warning_summary["warning"].apply(
            lambda x: x[:50] + "..." if len(x) > 50 else x
        )

        fig = px.bar(
            warning_summary,
            x="warning_short",
            y="count",
            color="aggregator",
            title="Top Warnings by Aggregator",
            labels={"warning_short": "Warning Type", "count": "Total Occurrences"},
        )

        fig.update_layout(
            template="plotly_white", height=600, xaxis_tickangle=-45, showlegend=True
        )

        return fig

    @staticmethod
    def create_quality_scorecard(df):
        """Create a comprehensive quality scorecard"""
        if df.empty:
            return "No quality data available"

        # Calculate overall metrics
        overall_metrics = {
            "Total Sessions": len(df),
            "Sessions with Quality Data": df["overall_quality"].notna().sum(),
            "Avg Completeness": df["overall_completeness"].mean(),
            "Avg Valid Ratio": df["valid_ratio"].mean(),
            "Total Valid Flights": df["valid_flights"].sum(),
            "Total Invalid Flights": df["invalid_flights"].sum(),
            "Overall Success Rate": (
                df["valid_flights"].sum()
                / (df["valid_flights"].sum() + df["invalid_flights"].sum())
                if (df["valid_flights"].sum() + df["invalid_flights"].sum()) > 0
                else 0
            ),
        }

        # Create scorecard HTML
        scorecard_html = """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; color: white;">
            <h2 style="margin-top: 0;">Data Quality Scorecard</h2>
        """

        for key, value in overall_metrics.items():
            if isinstance(value, float):
                display_value = f"{value:.2%}" if "%" in key else f"{value:.2f}"
            else:
                display_value = str(value)

            scorecard_html += f"""
            <div style="margin: 10px 0;">
                <div style="font-weight: bold; font-size: 14px;">{key}</div>
                <div style="font-size: 24px; font-weight: bold;">{display_value}</div>
            </div>
            """

        scorecard_html += "</div>"

        return scorecard_html

    @staticmethod
    def plot_correlation_matrix(df):
        """Plot correlation between different quality metrics"""
        if df.empty:
            return px.imshow(title="No quality data available")

        # Select numeric columns for correlation
        numeric_cols = [
            "overall_completeness",
            "valid_ratio",
            "completeness_ratio",
            "avg_completeness",
            "total_warnings",
            "valid_flights",
            "invalid_flights",
        ]

        numeric_df = df[numeric_cols].dropna()

        if numeric_df.empty:
            return px.imshow(title="No numeric quality data available")

        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()

        fig = px.imshow(
            corr_matrix,
            title="Quality Metrics Correlation Matrix",
            color_continuous_scale="RdBu",
            zmin=-1,
            zmax=1,
            aspect="auto",
            text_auto=True,
        )

        fig.update_layout(template="plotly_white", height=500)

        return fig
