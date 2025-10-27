import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import pandas as pd
import matplotlib.pyplot as plt
import re

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY not found. Please add it in your .env file.")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Financial Analysis", layout="wide")

# --- HEADER ---
st.title("📈 AI Financial Analysis Dashboard")

# --- USER INPUT ---
col1, col2 = st.columns([2, 1])

with col1:
    company_name = st.text_input(
        "🏢 Company Name", placeholder="Enter company name (e.g. Reliance, HDFC, Tata Motors)"
    )
with col2:
    file_upload = st.file_uploader("📄 Upload Financial Report (optional)", type=["pdf", "xbrl"])

analyze_button = st.button("🚀 Analyze Financials")

# --- ANALYSIS LOGIC ---
if analyze_button:
    if not company_name and not file_upload:
        st.warning("⚠️ Please enter a company name or upload a financial file.")
    else:
        with st.spinner("Analyzing financial data..."):
            if company_name:
                prompt = (
                    f"Generate a detailed financial analysis report of {company_name}, "
                    f"including market capitalization, annual performance, and latest quarterly results. "
                    f"Include numerical data in tabular form if possible."
                )
            else:
                prompt = (
                    "Analyze the uploaded financial document (PDF/XBRL) "
                    "and summarize company financial performance with trends and key metrics."
                )

            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_completion_tokens=1024,
                top_p=1
            )

            result = completion.choices[0].message.content
            st.session_state["report_text"] = result
            st.success("✅ Analysis Completed Successfully!")
            st.write(result)

# --- TOOLS SECTION ---
if "report_text" in st.session_state:
    st.divider()
    st.subheader("🧠 Smart Tools for Better Understanding")

    # --- New Visualize Button ---
    if st.button("📊 Visualize Data (Graphs, Charts, Piecharts)"):
        # Sample Financial DataFrame
        df = pd.DataFrame({
            "Parameter": ["Revenue", "Profit", "Expenses", "Market Cap"],
            "Value (₹ Cr)": [12000, 1200, 8000, 120000]
        })

        st.markdown("### 📉 Bar Chart")
        st.bar_chart(df.set_index("Parameter"))

        st.markdown("### 📈 Line Chart")
        st.line_chart(df.set_index("Parameter"))

        st.markdown("### 🥧 Pie Chart")
        fig, ax = plt.subplots()
        ax.pie(df["Value (₹ Cr)"], labels=df["Parameter"], autopct='%1.1f%%', startangle=90)
        ax.axis("equal")
        st.pyplot(fig)

    # --- Two Buttons (Summary + Table) ---
    col1, col2 = st.columns(2)

    # 1️⃣ Auto Summary
    with col1:
        if st.button("📝 Auto Summarize"):
            with st.spinner("Summarizing report..."):
                summary_prompt = (
                    f"Summarize the following financial report in 5 short bullet points:\n\n"
                    f"{st.session_state['report_text']}"
                )
                summary_completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.7
                )
                summary = summary_completion.choices[0].message.content
                st.markdown("### 📋 Summary")
                st.write(summary)

    # 2️⃣ Show Table
    with col2:
        if st.button("📋 Show Table"):
            df = pd.DataFrame({
                "Parameter": ["Revenue", "Profit", "Expenses", "Market Cap"],
                "Value": ["₹12,000 Cr", "₹1,200 Cr", "₹8,000 Cr", "₹1.2L Cr"]
            })
            st.markdown("### 🧾 Financial Table")
            st.table(df)
