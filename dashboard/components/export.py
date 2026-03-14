"""
CSV export component for the JESUS Company Cash Management System.
Provides download buttons for exporting data to CSV.
"""
import streamlit as st
import pandas as pd
import io
from typing import List, Dict
from datetime import datetime


def export_to_csv(data: List[Dict], filename: str, label: str = "Download CSV") -> None:
    """
    Render a CSV download button for a list of dictionaries.

    Args:
        data: List of dictionaries to export
        filename: Base filename (without extension)
        label: Button label text
    """
    if not data:
        st.caption("No data to export")
        return

    df = pd.DataFrame(data)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"{filename}_{timestamp}.csv"

    st.download_button(
        label=label,
        data=csv_data,
        file_name=full_filename,
        mime="text/csv"
    )


def export_dataframe_to_csv(df: pd.DataFrame, filename: str, label: str = "Download CSV") -> None:
    """
    Render a CSV download button for a pandas DataFrame.

    Args:
        df: DataFrame to export
        filename: Base filename (without extension)
        label: Button label text
    """
    if df.empty:
        st.caption("No data to export")
        return

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"{filename}_{timestamp}.csv"

    st.download_button(
        label=label,
        data=csv_data,
        file_name=full_filename,
        mime="text/csv"
    )
