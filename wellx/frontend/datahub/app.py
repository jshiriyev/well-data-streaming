import io
import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Table Join Playground", layout="wide")
st.title("Excel Table Join Playground")

st.markdown(
    "Upload multiple Excel files, inspect their columns, "
    "and interactively join them in different ways."
)

# --- SIDEBAR: file upload ---
st.sidebar.header("1. Upload Excel files")
uploaded_files = st.sidebar.file_uploader(
    "Upload one or more .xlsx files",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("⬅️ Upload some Excel files from the sidebar to get started.")
    st.stop()

# Read all uploaded files into dataframes
dfs = {}
for file in uploaded_files:
    # Use the filename (without extension) as the key
    name = os.path.splitext(file.name)[0]
    try:
        df = pd.read_excel(file)
        dfs[name] = df
    except Exception as e:
        st.error(f"Error reading {file.name}: {e}")

if not dfs:
    st.error("No valid Excel files were loaded.")
    st.stop()

table_names = list(dfs.keys())

# --- Show overview of tables and columns ---
st.header("Available Tables & Columns")

for name, df in dfs.items():
    with st.expander(f"📄 {name}  (rows: {len(df)}, columns: {len(df.columns)})"):
        st.write("**Columns:**")
        st.write(list(df.columns))
        st.write("**Sample (top 5 rows):**")
        st.dataframe(df.head())

st.markdown("---")

# --- JOIN CONFIGURATION ---
st.header("Build a Join")

left_name = st.selectbox("Left table", table_names, key="left_table")
right_candidates = [t for t in table_names if t != left_name]
if not right_candidates:
    st.warning("Upload at least two tables to perform a join.")
    st.stop()

right_name = st.selectbox("Right table", right_candidates, key="right_table")

left_df = dfs[left_name]
right_df = dfs[right_name]

st.subheader("Join Keys")

col1, col2 = st.columns(2)
with col1:
    left_keys = st.multiselect(
        f"Choose key column(s) from **{left_name}**",
        options=list(left_df.columns),
        key="left_keys"
    )
with col2:
    right_keys = st.multiselect(
        f"Choose key column(s) from **{right_name}**",
        options=list(right_df.columns),
        key="right_keys"
    )

join_type = st.selectbox(
    "Join type",
    options=["inner", "left", "right", "outer"],
    index=0
)

if st.button("Run Join"):
    if not left_keys or not right_keys:
        st.error("Please select key column(s) for both tables.")
    elif len(left_keys) != len(right_keys):
        st.error("Number of key columns must match on left and right.")
    else:
        try:
            merged = left_df.merge(
                right_df,
                how=join_type,
                left_on=left_keys,
                right_on=right_keys,
                suffixes=(f"_{left_name}", f"_{right_name}")
            )

            st.success(
                f"Joined **{left_name}** and **{right_name}** with a "
                f"**{join_type}** join. Result: {len(merged)} rows, "
                f"{len(merged.columns)} columns."
            )

            st.subheader("Joined Table (preview)")
            st.dataframe(merged.head(200))  # show first 200 rows

            # Download result as CSV
            csv_buf = io.StringIO()
            merged.to_csv(csv_buf, index=False)
            st.download_button(
                label="⬇️ Download joined table as CSV",
                data=csv_buf.getvalue(),
                file_name=f"{left_name}_{right_name}_{join_type}_join.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Error during join: {e}")
