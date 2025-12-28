# app.py
import streamlit as st
import pandas as pd
from quality_visualizations import QualityVisualizations
from database import FlightDataVisualizer
from visualizations import FlightVisualizations

# Set page config
st.set_page_config(page_title="Flight Price Analytics", page_icon="✈️", layout="wide")

# Initialize database connection
@st.cache_resource
def init_visualizer():
    return FlightDataVisualizer()


visualizer = init_visualizer()

# Sidebar for navigation
st.sidebar.title("✈️ Flight Analytics")

# Update sidebar to include quality dashboard
page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Best Flights",
        "Route Combinations",
        "Price Trends",
        "Aggregator Analysis",
        "Data Quality",
    ],
)


# Load data
@st.cache_data(ttl=300)
def load_data():
    best_flights = visualizer.fetch_best_flights()
    best_combos = visualizer.fetch_best_combos()
    price_ts = visualizer.fetch_price_timeseries()
    return best_flights, best_combos, price_ts


best_flights_df, best_combos_df, price_ts_df = load_data()

if page == "Best Flights":
    st.title("Best Flight Prices Analysis")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Best Flight Prices Overview")
        st.dataframe(
            best_flights_df.head(100), use_container_width=True, hide_index=True
        )

    with col2:
        st.subheader("Filters")
        route_type_filter = st.multiselect(
            "Route Type",
            options=best_flights_df["route_type"].unique(),
            default=best_flights_df["route_type"].unique(),
        )

        aggregator_filter = st.multiselect(
            "Site Aggregator",
            options=best_flights_df["site_aggregator"].unique(),
            default=best_flights_df["site_aggregator"].unique(),
        )

    # Filter data
    filtered_df = best_flights_df[
        (best_flights_df["route_type"].isin(route_type_filter))
        & (best_flights_df["site_aggregator"].isin(aggregator_filter))
    ]

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        fig1 = FlightVisualizations.plot_best_prices_comparison(filtered_df)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Price Statistics")
        stats_df = (
            filtered_df.groupby(["route_type", "site_aggregator"])
            .agg({"best_price": ["mean", "min", "max", "count"]})
            .round(2)
        )
        st.dataframe(stats_df, use_container_width=True)

elif page == "Route Combinations":
    st.title("Best Route Combinations")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Combined Route Prices Distribution")
        fig = FlightVisualizations.plot_combo_price_distribution(best_combos_df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Summary Statistics")
        st.metric("Total Combinations", len(best_combos_df))
        st.metric("Average Price", f"{best_combos_df['total_price'].mean():.2f}")
        st.metric("Minimum Price", f"{best_combos_df['total_price'].min():.2f}")

        # Currency distribution
        currency_dist = best_combos_df["currency"].value_counts()
        st.write("**Currency Distribution:**")
        st.dataframe(currency_dist, use_container_width=True)

    # Show data table
    st.subheader("Route Combinations Data")
    st.dataframe(best_combos_df, use_container_width=True, hide_index=True)

elif page == "Price Trends":
    st.title("Flight Price Trends Over Time")

    # Request ID selector
    request_ids = price_ts_df["request_id"].unique()
    selected_request = st.selectbox(
        "Select Request ID (or leave empty for all):",
        options=["All"] + list(request_ids[:20]),
    )

    if selected_request != "All":
        ts_data = price_ts_df[price_ts_df["request_id"] == selected_request]
        title_suffix = f"for Request {selected_request}"
    else:
        ts_data = price_ts_df
        title_suffix = "Across All Requests"

    # Plot timeseries
    fig = FlightVisualizations.plot_price_timeseries(
        ts_data, selected_request if selected_request != "All" else None
    )
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap
    st.subheader(f"Price Heatmap {title_suffix}")
    heatmap_fig = FlightVisualizations.plot_price_heatmap(ts_data)
    st.plotly_chart(heatmap_fig, use_container_width=True)

    # Data table
    with st.expander("View Time Series Data"):
        st.dataframe(
            ts_data.sort_values("price_date", ascending=False), use_container_width=True
        )

elif page == "Aggregator Analysis":
    st.title("Site Aggregator Performance Analysis")

    fig = FlightVisualizations.plot_aggregator_performance(best_flights_df)
    st.plotly_chart(fig, use_container_width=True)

    # Detailed statistics
    st.subheader("Detailed Aggregator Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Aggregators", best_flights_df["site_aggregator"].nunique())

    with col2:
        st.metric("Total Price Records", len(best_flights_df))

    with col3:
        avg_price = best_flights_df["best_price"].mean()
        st.metric("Overall Average Price", f"{avg_price:.2f}")

    # Aggregator ranking
    st.subheader("Aggregator Ranking by Best Prices Found")
    ranking_df = (
        best_flights_df.groupby("site_aggregator")
        .agg({"best_price": ["count", "mean", "min", "max"]})
        .round(2)
    )

    ranking_df.columns = ["Count", "Average Price", "Best Price", "Worst Price"]
    ranking_df = ranking_df.sort_values("Best Price")

    st.dataframe(ranking_df, use_container_width=True)
    
elif page == "Data Quality":
    st.title("Search Session Data Quality Analysis")
    
    # Load and parse quality data
    @st.cache_data(ttl=300)
    def load_quality_data():
        sessions_df = visualizer.fetch_search_sessions(days_back=30)
        quality_df = QualityVisualizations.parse_quality_json(sessions_df)
        return sessions_df, quality_df
    
    sessions_df, quality_df = load_quality_data()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sessions", len(sessions_df))
    with col2:
        st.metric("Sessions with Quality Data", quality_df['session_id'].nunique())
    with col3:
        avg_comp = quality_df['overall_completeness'].mean() if not quality_df.empty else 0
        st.metric("Avg Completeness", f"{avg_comp:.2%}")
    with col4:
        valid_ratio = quality_df['valid_ratio'].mean() if not quality_df.empty else 0
        st.metric("Avg Valid Ratio", f"{valid_ratio:.2%}")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        if not quality_df.empty:
            min_date = quality_df['search_at'].min().date()
            max_date = quality_df['search_at'].max().date()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                filtered_quality = quality_df[
                    (quality_df['search_at'].dt.date >= date_range[0]) &
                    (quality_df['search_at'].dt.date <= date_range[1])
                ]
            else:
                filtered_quality = quality_df
        else:
            filtered_quality = quality_df
    
    with col2:
        aggregator_filter = st.multiselect(
            "Site Aggregator",
            options=quality_df['site_aggregator'].unique() if not quality_df.empty else [],
            default=quality_df['site_aggregator'].unique() if not quality_df.empty else []
        )
        
        if aggregator_filter and not quality_df.empty:
            filtered_quality = filtered_quality[
                filtered_quality['site_aggregator'].isin(aggregator_filter)
            ]
    
    # Quality Scorecard
    st.subheader("Quality Overview")
    scorecard_html = QualityVisualizations.create_quality_scorecard(filtered_quality)
    st.html(scorecard_html)
    
    # Tab layout for different quality views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Trends", "Distribution", "Aggregator Comparison", "Warnings Analysis"
    ])
    
    with tab1:
        st.subheader("Quality Trends Over Time")
        trend_fig = QualityVisualizations.plot_quality_trends(filtered_quality)
        st.plotly_chart(trend_fig, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Quality Distribution")
            dist_fig = QualityVisualizations.plot_quality_distribution(filtered_quality)
            st.plotly_chart(dist_fig, use_container_width=True)
        
        with col2:
            st.subheader("Metrics Correlation")
            corr_fig = QualityVisualizations.plot_correlation_matrix(filtered_quality)
            st.plotly_chart(corr_fig, use_container_width=True)
    
    with tab3:
        st.subheader("Aggregator Quality Comparison")
        agg_fig = QualityVisualizations.plot_aggregator_quality_comparison(filtered_quality)
        st.plotly_chart(agg_fig, use_container_width=True)
    
    with tab4:
        st.subheader("Warning Analysis")
        warning_fig = QualityVisualizations.plot_warnings_analysis(filtered_quality)
        st.plotly_chart(warning_fig, use_container_width=True)
        
        # Show raw warning data
        with st.expander("View Detailed Warning Data"):
            if not filtered_quality.empty:
                warning_details = filtered_quality[['search_at', 'site_aggregator', 
                                                   'total_warnings', 'top_warning']]
                st.dataframe(warning_details.sort_values('search_at', ascending=False), 
                           use_container_width=True)
    
    # Raw data explorer
    st.subheader("Quality Data Explorer")
    with st.expander("View Raw Quality Data"):
        if not sessions_df.empty:
            # Parse and display quality JSON in a readable format
            display_cols = ['id', 'search_at', 'site_aggregator', 'status', 'quality']
            st.dataframe(sessions_df[display_cols], use_container_width=True)
            
            # Option to view individual session details
            selected_session = st.selectbox(
                "Select session to view detailed quality metrics:",
                options=sessions_df['id'].tolist()[:100]
            )
            
            if selected_session:
                session_data = sessions_df[sessions_df['id'] == selected_session].iloc[0]
                if session_data['quality']:
                    st.json(session_data['quality'])
    
    # Export functionality
    st.subheader("Export Quality Report")
    if not filtered_quality.empty:
        # Convert to CSV for download
        csv = filtered_quality.to_csv(index=False)
        st.download_button(
            label="Download Quality Data as CSV",
            data=csv,
            file_name="quality_metrics.csv",
            mime="text/csv"
        )

# Footer
st.sidebar.markdown("---")

if 'quality_df' in locals() and not quality_df.empty:
    st.sidebar.subheader("📊 Quick Quality Stats")
    
    # Calculate quick stats
    recent_quality = quality_df[quality_df['search_at'] > pd.Timestamp.now() - pd.Timedelta(days=7)]
    
    if not recent_quality.empty:
        avg_quality = recent_quality['overall_completeness'].mean()
        best_aggregator = recent_quality.groupby('site_aggregator')['overall_completeness'].mean().idxmax()
        
        st.sidebar.metric("7-day Avg Quality", f"{avg_quality:.1%}")
        st.sidebar.metric("Best Aggregator", best_aggregator)
        
        # Quality alert
        if avg_quality < 0.7:
            st.sidebar.warning("⚠️ Quality below 70% threshold")
        elif avg_quality < 0.85:
            st.sidebar.info("ℹ️ Quality could be improved")
        else:
            st.sidebar.success("✅ Quality is good")
            
st.sidebar.info(
    """
    **Data Sources:**
    - `gold_request_best_flights_mv`
    - `gold_request_best_route_combo_mv`
    - `gold_request_price_timeseries_mv`
    - `data quality from sessions`
    """
)
