import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import pandas as pd
import matplotlib.pyplot as plt
import re
import io
import json

# For PDF text extraction
try:
    import PyPDF2
except ImportError:
    st.error("❌ PyPDF2 is required. Install with: pip install PyPDF2")
    st.stop()

# Load environment
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("❌ GROQ_API_KEY not found in .env")
    st.stop()

client = Groq(api_key=api_key)
st.set_page_config(page_title="AI Financial Analysis", layout="wide")
st.title("📈 AI Financial Analysis Dashboard")

# ---------------- SMART PROMPT LIBRARY ---------------- #

BUSINESS_MODEL_PROMPT = """
Explain the business model of {company_name}.
Describe its main revenue streams, customer segments, value proposition, and cost structure.
Summarize in 4-5 bullet points.
If available, use insights from the company’s financial statements or annual report.
"""

MANAGEMENT_COMMENTARY_PROMPT = """
Summarize the recent management commentary for {company_name}.
Highlight key themes such as business outlook, challenges, opportunities, and strategic decisions.
If available, use management quotes from quarterly or annual reports.
"""

RED_FLAGS_PROMPT = """
Identify and explain potential red flags for {company_name}.
Include points such as:
- Governance or regulatory issues
- Declining margins or rising debt
- Frequent leadership changes
- Auditor resignations or lawsuits
Provide a short summary table if possible.
"""

KEY_PRODUCTS_PROMPT = """
Create a table of key products or services offered by {company_name}.
Include columns:
Product/Service | Segment | Revenue Contribution | Key Market | Growth Trend
"""

EVOLUTION_PROMPT = """
Describe the evolution of {company_name} over the last 3 years.
Cover:
- Business expansion or restructuring
- Financial performance trends
- New product launches
- Mergers, acquisitions, or partnerships
Present in a concise 3-year timeline format.
"""

STOCK_PERFORMANCE_PROMPT = """
Based on recent financial data and management commentary, analyze how the stock of {company_name} is expected to perform in the next 6–12 months.
Include technical and fundamental insights where possible.
Summarize risks and catalysts.
"""

GROWTH_OUTLOOK_PROMPT = """
Project the growth outlook for {company_name} over the next 3 years.
Include potential drivers (sector growth, policy, expansion) and risks.
Summarize with key metrics like Revenue CAGR, EPS growth, and ROE trends.
"""

GUIDANCE_VS_DELIVERY_PROMPT = """
Analyze management’s past guidance vs actual delivery for {company_name}.
Create a table with columns:
Year | Guidance Given | Actual Results | Deviation (%) | Remarks
Highlight whether management has been consistent or overpromising.
"""

DOC_ANALYSIS_PROMPT = """
Using the 141 available documents of {company_name}, extract key insights related to:
"{user_query}"
Summarize with supporting numbers and short bullet points.
"""

def get_financial_prompt(query, company_name):
    """Auto-selects best prompt based on user query"""
    query = query.lower()
    if "business model" in query:
        return BUSINESS_MODEL_PROMPT.format(company_name=company_name)
    elif "management" in query and "commentary" in query:
        return MANAGEMENT_COMMENTARY_PROMPT.format(company_name=company_name)
    elif "red flag" in query:
        return RED_FLAGS_PROMPT.format(company_name=company_name)
    elif "key product" in query or "service" in query:
        return KEY_PRODUCTS_PROMPT.format(company_name=company_name)
    elif "evolution" in query:
        return EVOLUTION_PROMPT.format(company_name=company_name)
    elif "stock" in query or "performance" in query:
        return STOCK_PERFORMANCE_PROMPT.format(company_name=company_name)
    elif "growth" in query or "outlook" in query:
        return GROWTH_OUTLOOK_PROMPT.format(company_name=company_name)
    elif "guidance" in query:
        return GUIDANCE_VS_DELIVERY_PROMPT.format(company_name=company_name)
    else:
        return DOC_ANALYSIS_PROMPT.format(company_name=company_name, user_query=query)

# ---------------- MAIN INPUT SECTION ---------------- #

col1, col2 = st.columns([2, 1])
with col1:
    company_name = st.text_input("🏢 Company Name", placeholder="Enter company name (e.g. Reliance, HDFC, Tata Motors)")
with col2:
    file_upload = st.file_uploader("📄 Upload Financial Report (optional)", type=["pdf", "xbrl"])

query_input = st.text_input("💬 Ask SageApla (e.g. What are the red flags in HDFC Bank?)")
analyze_button = st.button("🚀 SageAlpha AI")

# ---------------- ANALYSIS LOGIC ---------------- #

if analyze_button:
    if not company_name and not file_upload:
        st.warning("⚠️ Enter a company name or upload a file.")
    elif query_input:
        with st.spinner("🔍 Generating SageAlpha finance response..."):
            prompt = get_financial_prompt(query_input, company_name or "the company")
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=900
            )
            report_text = completion.choices[0].message.content
            st.session_state["report_text"] = report_text
            st.success("✅ SageAlpha Finance Analysis Completed!")
            st.markdown(report_text)

    elif file_upload:
        with st.spinner("📑 Processing uploaded report..."):
            try:
                file_content = file_upload.read()
                if file_upload.name.endswith(".pdf"):
                    reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    text = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
                else:
                    text = file_content.decode("utf-8")

                analysis_prompt = f"Analyze the following company financial document and extract major insights, key metrics, and financial health summary:\n\n{text[:4000]}"
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": analysis_prompt}],
                    temperature=0.5,
                    max_tokens=1024
                )
                report_text = completion.choices[0].message.content
                st.session_state["report_text"] = report_text
                st.success("✅ File Analysis Done!")
                st.markdown(report_text)
            except Exception as e:
                st.error(f"❌ Error processing file: {e}")

# ---------------- SMART TOOLS ---------------- #

if "report_text" in st.session_state:
    st.divider()
    st.subheader("🧠 Smart Tools for Better Understanding")

    @st.cache_data
    def extract_metrics(report_text):
        extract_prompt = (
            f"You are a financial data extractor. From the report below, extract ONLY:\n"
            f"revenue, profit, expenses, and market_cap (in Cr or billions).\n"
            f"Output JSON only:\n"
            f'{{"revenue": 0, "profit": 0, "expenses": 0, "market_cap": 0, "currency": "₹"}}\n\n'
            f"Report: {report_text[:2000]}"
        )
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Output only valid JSON."},
                    {"role": "user", "content": extract_prompt},
                ],
                temperature=0.0,
                max_tokens=150,
            )
            raw = completion.choices[0].message.content.strip()
            if "```" in raw:
                raw = re.sub(r"```(json)?", "", raw).strip()
            return json.loads(raw)
        except Exception:
            return {"revenue": 0, "profit": 0, "expenses": 0, "market_cap": 0, "currency": "₹"}

    metrics = extract_metrics(st.session_state["report_text"])

    if st.button("📊 Visualize Data (Graphs, Charts, Piecharts)"):
        df = pd.DataFrame({
            "Parameter": ["Revenue", "Profit", "Expenses", "Market Cap"],
            "Value": [metrics["revenue"], metrics["profit"], metrics["expenses"], metrics["market_cap"]]
        })
        st.bar_chart(df.set_index("Parameter"))
        st.line_chart(df.set_index("Parameter"))
        fig, ax = plt.subplots()
        ax.pie(df["Value"], labels=df["Parameter"], autopct='%1.1f%%')
        st.pyplot(fig)

    colA, colB = st.columns(2)
    with colA:
        if st.button("📝 Auto Summarize"):
            with st.spinner("Summarizing..."):
                summary_prompt = f"Summarize this financial analysis in 5 short bullet points:\n\n{st.session_state['report_text']}"
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.6,
                    max_tokens=300
                )
                st.markdown("### 📋 Summary")
                st.markdown(completion.choices[0].message.content)

    with colB:
        if st.button("📋 Show Table"):
            table = pd.DataFrame({
                "Parameter": ["Revenue", "Profit", "Expenses", "Market Cap"],
                "Value": [
                    f"{metrics['revenue']} {metrics['currency']} Cr" if metrics['revenue'] else "N/A",
                    f"{metrics['profit']} {metrics['currency']} Cr" if metrics['profit'] else "N/A",
                    f"{metrics['expenses']} {metrics['currency']} Cr" if metrics['expenses'] else "N/A",
                    f"{metrics['market_cap']} {metrics['currency']} Cr" if metrics['market_cap'] else "N/A"
                ]
            })
            st.markdown("### 🧾 Financial Table")
            st.table(table)
