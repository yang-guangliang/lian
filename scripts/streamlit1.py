import streamlit as st
import pandas as pd

st.header("垂直排列")
# df1 = pd.read_feather("/home/rainy/projects/lian_open_source250509/lian/tests/lian_workspace/semantic_p2/s2space_p2.bundle0")
df2 = pd.read_feather("/home/rainy/projects/lian_open_source250509/lian/tests/lian_workspace/gir/gir.bundle0")
# st.dataframe(df1, use_container_width=True)  
st.dataframe(df2, use_container_width=True) 
