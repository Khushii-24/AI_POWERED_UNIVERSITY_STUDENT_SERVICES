import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE = "http://127.0.0.1:8000"
STUDENT_ID = "123"

st.set_page_config(page_title="University AI Assistant", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Chat", "Documents", "Records"])

if page == "Chat":
    st.title("AI Assistant")
    
    as_of_date = st.sidebar.date_input("As of Date", datetime.now())
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and "details" in msg:
                d = msg["details"]
                st.caption(f"Badge: {d.get('answer_type')}")
                with st.expander("Details (Citations / Tools / Rules)"):
                    st.json(d)
                    
    prompt = st.chat_input("Ask a question...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            try:
                res = requests.post(f"{API_BASE}/ask", json={"question": prompt, "as_of_date": str(as_of_date)}, headers={"student-id": STUDENT_ID})
                if res.status_code == 200:
                    data = res.json()
                    st.markdown(data['answer'])
                    st.caption(f"Badge: {data['answer_type']}")
                    with st.expander("Details (Citations / Tools / Rules)"):
                        st.json(data)
                    st.session_state.messages.append({"role": "assistant", "content": data['answer'], "details": data})
                else:
                    st.error(f"API Error: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}. Is the API running?")

elif page == "Documents":
    st.title("Documents Management")
    st.write("Upload and ingest university policy documents.")
    
    with st.form("ingest_form"):
        title = st.text_input("Title")
        doc_type = st.selectbox("Doc Type", ["CIRCULAR", "ORDINANCE", "ACT"])
        auth_level = st.number_input("Authority Level (1=Highest)", min_value=1, max_value=5, value=3)
        version = st.text_input("Version", "1.0")
        eff_from = st.date_input("Effective From")
        uploaded_file = st.file_uploader("Document (Text or MD)")
        
        submitted = st.form_submit_button("Ingest")
        if submitted and uploaded_file:
            st.info("Mock ingest - would call /ingest API")
            
    st.subheader("Source Register")
    try:
        res = requests.get(f"{API_BASE}/sources")
        if res.status_code == 200:
            sources = res.json().get('sources', [])
            st.dataframe(pd.DataFrame(sources))
        else:
            st.error("Failed to load sources.")
    except:
        st.warning("Could not connect to API to fetch sources.")

elif page == "Records":
    st.title("My Records")
    st.write("Upload your synthetic data CSVs.")
    
    st.subheader("Upload Records")
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    if uploaded_file:
        st.info("Mock upload - would call /records/load")
        
    st.subheader("My Attendance (Mock Data)")
    try:
        # Mock pulling from local sqlite for UI demo
        import sqlite3
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'university.db')
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM attendance WHERE student_id='{STUDENT_ID}'", conn)
        if not df.empty:
            df['percentage'] = (df['classes_attended'] / df['classes_held']) * 100
            st.dataframe(df)
        else:
            st.write("No attendance records found.")
        conn.close()
    except Exception as e:
        st.error(f"Error fetching attendance: {e}")
