from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / "rollrcoast.csv"
df = pd.read_csv(DATA_PATH)

st.title("Time vs. Difficulty")
st.write("Does a tower's difficulty determine its time?")
st.line_chart(data=df, x="NUM", y="TIME [s]", x_label="Tower Difficulty", y_label="Beat Time", color="#FF0000")
st.bar_chart(df, x="NUM", y="TIME [s]")