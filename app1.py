import streamlit as st
import pandas as pd
import sqlite3
import io

# ---------------- DB CONNECTION ---------------- #
def get_connection():
    return sqlite3.connect("logs.db")


# ---------------- AUTH FUNCTION ---------------- #
def check_login(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ SQLite uses ?
    query = "SELECT * FROM users WHERE username=? AND password=?"
    cursor.execute(query, (username, password))

    result = cursor.fetchone()
    conn.close()

    return result is not None


# ---------------- FETCH DATA ---------------- #
def fetch_data(table, start_date, end_date, vin):
    conn = get_connection()

    # ✅ SQLite query (no backticks, use ?)
    query = f"""
        SELECT * FROM {table}
        WHERE DATE(Timestamp_ist) BETWEEN ? AND ?
        AND vin = ?
    """

    df = pd.read_sql(query, conn, params=(start_date, end_date, vin))
    conn.close()

    return df


# ---------------- SESSION STATE ---------------- #
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ---------------- LOGIN PAGE ---------------- #
if not st.session_state.logged_in:

    st.title("🔐 Login")

    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Login"):
        if check_login(username, password):
            st.session_state.logged_in = True
            st.success("Login successful ✅")
            st.rerun()
        else:
            st.error("Invalid username or password ❌")


# ---------------- MAIN APP ---------------- #
else:

    st.title("🚗 Log Download Dashboard")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("📅 From Date")

    with col2:
        end_date = st.date_input("📅 To Date")

    vin = st.text_input("🚗 Enter VIN (Example: CAR1001)")

    if st.button("🔍 Get Logs"):

        if not vin:
            st.warning("Please enter VIN")
            st.stop()

        tables = ["Alert", "Periodic", "Event", "Hygiene", "Ecosense"]
        all_data = {}

        with st.spinner("Fetching data... ⏳"):

            # Process tables in pairs (2 per row)
            for i in range(0, len(tables), 2):

                cols = st.columns(2)

                for j in range(2):
                    if i + j < len(tables):

                        table = tables[i + j]
                        df = fetch_data(table, start_date, end_date, vin)

                        with cols[j]:
                            st.subheader(f"📂 {table}")

                            if df.empty:
                                st.warning("No data")
                            else:
                                st.write(f"Top 10 / {len(df)} rows")
                                st.dataframe(df.head(10), use_container_width=True)
                                all_data[table] = df

        # ---------------- EXCEL DOWNLOAD ---------------- #
        if all_data:
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for table, df in all_data.items():
                    df.to_excel(writer, sheet_name=table, index=False)

            output.seek(0)

            st.download_button(
                label="⬇️ Download Excel Report",
                data=output,
                file_name=f"{vin}_logs.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("No data available")