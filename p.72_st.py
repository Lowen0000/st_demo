import streamlit as st
import numpy as py
import pandas as pd

st.title("🏓運動數據分析展示")

data=pd.read_csv('sbdv_mid_exam.csv')

df=data[['weekly_training_hours','fitness_score']]

st.write('運動數據：')
st.dataframe(df)
st.write('線圖展示')
st.line_chart(df)
st.write('長條圖')
st.bar_chart(df)