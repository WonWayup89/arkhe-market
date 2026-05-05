import pandas as pd
import streamlit as st

def show_table(df: pd.DataFrame, height: int = 320):
    st.dataframe(df, width="stretch", height=height, hide_index=True)
