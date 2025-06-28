import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio


# --- Configuration ---
# Define the path to your CSV file.
# This assumes dashboard_app.py is in the same directory as the 'output' folder.
CSV_FILE_PATH = os.path.join(os.path.dirname(__file__), "output", "ceresne_flats.csv")

# Additional debug & environment re-setup required for the change below, skipped for now
#  --- Plotly Locale Setup for European Decimal Formatting ---
# Set default template (already there, but good to place near locale setup)
# pio.templates.default = "plotly_white"
# Set locale for numbers
# pio.locales.set_locale("de")


# --- Load Data ---
@st.cache_data  # Cache the data loading to improve performance
@st.cache_data
# --- Load Data ---
@st.cache_data
def load_data(path):
    """
    Load the data from a CSV file.

    Parameters:
    path (str): The path to the CSV file.

    Returns:
    pd.DataFrame: The loaded DataFrame with normalized column names.
    """
    try:
        # Add decimal=',' if the CSV uses commas for decimals (e.g., 123,45)
        df = pd.read_csv(path, decimal=",")

        # --- Column Name Normalization ---
        # 1. Strip leading/trailing whitespace (just in case, even if not obvious)
        df.columns = df.columns.str.strip()
        # 2. Convert all column names to lowercase (they already are, but good for consistency)
        df.columns = df.columns.str.lower()
        # 3. Replace spaces with underscores for easier programmatic access
        df.columns = df.columns.str.replace(" ", "_")
        # --- END NORMALIZATION ---

        # Define numeric columns using their NEW, NORMALIZED (snake_case) names
        numeric_cols = ["total_area", "rooms", "price_with_vat", "discounted_price"]

        # Convert relevant columns to numeric, handling potential non-numeric entries
        for col in numeric_cols:
            if col in df.columns:  # Check if the normalized column name exists
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                st.warning(
                    f"Normalized column '{col}' expected for numeric conversion was not found in the DataFrame. (Check your CSV headers and normalization logic)."
                )

        return df
    except FileNotFoundError:
        st.error(
            f"Error: CSV file not found at {path}. Please ensure the scraper has run and the file exists."
        )
        return pd.DataFrame()  # Return empty DataFrame on error
    except Exception as e:
        st.error(f"An error occurred while loading or processing the data: {e}")
        return pd.DataFrame()


# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Ceresne Flats Scraper Dashboard")
st.title("🏡 Ceresne Flats Data Dashboard")


df = load_data(CSV_FILE_PATH)

if not df.empty:
    st.subheader("Raw Scraped Data")
    st.dataframe(df)

    # You can remove this line after confirming it works, or keep for debugging
    # st.write("Normalized Columns for Plotting:", df.columns.tolist())

    st.markdown("---")

    st.subheader("Data Visualizations")

    # --- Chart 1: Price Distribution (Histogram) ---
    st.markdown("### 📊 Price Distribution")
    # Use the normalized column name 'price_with_vat'
    if "price_with_vat" in df.columns:
        fig_price_dist = px.histogram(
            df,
            x="price_with_vat",  # Use normalized name here
            nbins=30,
            title="Distribution of Prices with VAT",
            template="plotly_white",
        )
        fig_price_dist.update_layout(
            xaxis_title="Price with VAT (€)", yaxis_title="Number of Flats"
        )
        st.plotly_chart(fig_price_dist, use_container_width=True)
    else:
        st.warning(
            "`price_with_vat` column not found for price distribution chart after normalization."
        )

    # --- Chart 2: Number of Rooms Distribution (Bar Chart) ---
    st.markdown("### 🛏️ Number of Rooms Distribution")
    # Use the normalized column name 'rooms'
    if "rooms" in df.columns:
        # Ensure the column exists and is not entirely NaN before value_counts
        if not df["rooms"].dropna().empty:
            room_counts = df["rooms"].value_counts().sort_index().reset_index()
            room_counts.columns = [
                "rooms",
                "Count",
            ]  # Update column name for the new df too
            fig_rooms = px.bar(
                room_counts,
                x="rooms",  # Use normalized name here
                y="Count",
                title="Number of Rooms Distribution",
                template="plotly_white",
            )
            fig_rooms.update_layout(
                xaxis_title="Rooms", yaxis_title="Number of Listings"
            )
            st.plotly_chart(fig_rooms, use_container_width=True)
        else:
            st.warning(
                "`rooms` column found but contains no valid data for room distribution chart."
            )
    else:
        st.warning(
            "`rooms` column not found for room distribution chart after normalization."
        )

    # --- Chart 3: Total Area vs. Price (Scatter Plot) ---
    st.markdown("### 📏 Price vs. Total Area")
    # Use normalized column names 'total_area' and 'price_with_vat'
    if "total_area" in df.columns and "price_with_vat" in df.columns:
        # Filter out NaN values for plotting in both relevant columns
        plot_df = df.dropna(subset=["total_area", "price_with_vat"])
        fig_area_price = px.scatter(
            plot_df,
            x="total_area",  # Use normalized name here
            y="price_with_vat",  # Use normalized name here
            # Update hover_data to normalized names as well
            hover_data=["apartment_number", "floor", "rooms"],
            title="Price with VAT vs. Total Area",
            template="plotly_white",
        )
        fig_area_price.update_layout(
            xaxis_title="Total Area (m²)", yaxis_title="Price with VAT (€)"
        )
        st.plotly_chart(fig_area_price, use_container_width=True)
    else:
        st.warning(
            "`total_area` or `price_with_vat` column not found for area vs. price chart after normalization."
        )

    # --- Chart 4: Flats by Status (Pie Chart) ---
    st.markdown("### 📈 Flats by Status")
    # Use normalized column name 'status'
    if "status" in df.columns:
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = [
            "status",
            "Count",
        ]  # Update column name for the new df too
        fig_status = px.pie(
            status_counts,
            values="Count",
            names="status",  # Use normalized name here
            title="Distribution of Flats by Status",
            hole=0.3,  # Creates a donut chart
            template="plotly_white",
        )
        st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.warning(
            "`status` column not found for flats by status chart after normalization."
        )

    # You can add more charts here based on your data and interests!

else:
    st.info(
        "No data available to display charts. Please run the scraper to generate 'ceresne_flats.csv'."
    )

st.markdown("---")
st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
