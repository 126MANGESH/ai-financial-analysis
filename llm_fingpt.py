import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import pandas as pd
import matplotlib.pyplot as plt
import re
import io  # For handling file content in memory
import json  # For safe JSON parsing

# For PDF text extraction (install via: pip install PyPDF2)
try:
    import PyPDF2
except ImportError:
    st.error("❌ PyPDF2 is required for PDF processing. Install it with: `pip install PyPDF2`")
    st.stop()

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
            report_text = ""
            if company_name:
                # ✅ Analyze company name
                prompt = (
                    f"Generate a detailed financial analysis report of {company_name}, "
                    f"including market capitalization, annual performance, and latest quarterly results. "
                    f"Include numerical data in tabular form if possible. Structure the output with sections like 'Key Metrics' and use markdown for tables."
                )
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1024,  # Use max_tokens instead of max_completion_tokens (deprecated in newer Groq SDK)
                    top_p=1
                )
                report_text = completion.choices[0].message.content
                st.session_state["report_text"] = report_text
                st.success("✅ Analysis Completed Successfully!")
                st.markdown(report_text)
            
            elif file_upload:
                # ✅ Handle file upload
                file_content = file_upload.read()
                file_extension = file_upload.name.split('.')[-1].lower()
                
                if file_extension == 'pdf':
                    # Extract text from PDF
                    try:
                        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                        extracted_text = ""
                        for page in pdf_reader.pages:
                            extracted_text += page.extract_text() + "\n"
                        
                        if not extracted_text.strip():
                            st.error("❌ No text could be extracted from the PDF. It might be scanned or image-based.")
                        else:
                            # Analyze extracted text
                            analysis_prompt = (
                                f"Analyze the following financial report text and generate a detailed summary, "
                                f"including key metrics like revenue, profit, expenses, market cap, etc. "
                                f"Structure the output with sections like 'Key Metrics' (in markdown table) and 'Insights'. "
                                f"Limit to the most important data.\n\n"
                                f"Text: {extracted_text[:4000]}"  # Truncate for token limits; adjust as needed
                            )
                            completion = client.chat.completions.create(
                                model="llama-3.1-8b-instant",
                                messages=[{"role": "user", "content": analysis_prompt}],
                                temperature=0.5,  # Lower for more factual extraction
                                max_tokens=1024
                            )
                            report_text = completion.choices[0].message.content
                            st.session_state["report_text"] = report_text
                            st.success("✅ PDF Analysis Completed Successfully!")
                            st.markdown(report_text)
                    except Exception as e:
                        st.error(f"❌ Error processing PDF: {str(e)}")
                
                elif file_extension == 'xbrl':
                    # XBRL handling is more complex; basic text extraction for now
                    # For full XBRL parsing, consider libraries like python-xbrl (not included here)
                    st.warning("⚠️ XBRL support is basic. Extracting raw text for analysis.")
                    try:
                        # Treat XBRL as XML text
                        extracted_text = file_content.decode('utf-8')
                        analysis_prompt = (
                            f"Parse this XBRL financial data and extract key metrics (e.g., revenue, net income, assets) "
                            f"into a markdown table. Provide a summary of the financial health.\n\n"
                            f"Data: {extracted_text[:4000]}"  # Truncate
                        )
                        completion = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role": "user", "content": analysis_prompt}],
                            temperature=0.5,
                            max_tokens=1024
                        )
                        report_text = completion.choices[0].message.content
                        st.session_state["report_text"] = report_text
                        st.success("✅ XBRL Analysis Completed Successfully!")
                        st.markdown(report_text)
                    except Exception as e:
                        st.error(f"❌ Error processing XBRL: {str(e)}")
                
                else:
                    st.error("❌ Unsupported file type. Please upload PDF or XBRL.")

# --- TOOLS SECTION ---
if "report_text" in st.session_state:
    st.divider()
    st.subheader("🧠 Smart Tools for Better Understanding")

    # --- Improved Extract Structured Data for Dynamic Viz ---
    @st.cache_data
    def extract_metrics(report_text):
        # Better prompt for reliable JSON output
        extract_prompt = (
            f"You are a financial data extractor. From the following report, extract ONLY the values for: "
            f"revenue (total annual revenue in Cr or billions), profit (net profit in Cr or billions), "
            f"expenses (total expenses in Cr or billions), market_cap (in Cr or billions). "
            f"If not mentioned, use 0. Output EXACTLY this JSON format, nothing else:\n"
            f'{{"revenue": 12345, "profit": 1234, "expenses": 11111, "market_cap": 123456, "currency": "₹"}}\n\n'
            f"Report: {report_text[:2000]}"  # Limit input for better focus
        )
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You output ONLY valid JSON. No explanations."},
                    {"role": "user", "content": extract_prompt}
                ],
                temperature=0.0,  # Zero for deterministic output
                max_tokens=150
            )
            raw_output = completion.choices[0].message.content.strip()
            
            # Safe JSON parsing
            if raw_output.startswith('```json'):
                raw_output = raw_output.split('```json')[1].split('```')[0].strip()
            elif raw_output.startswith('```'):
                raw_output = raw_output.split('```')[1].strip()
            
            parsed = json.loads(raw_output)
            # Ensure all keys exist
            defaults = {"revenue": 0, "profit": 0, "expenses": 0, "market_cap": 0, "currency": "₹"}
            defaults.update(parsed)
            return defaults
        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"⚠️ Extraction failed (details: {str(e)}). Using defaults.")
            return {"revenue": 0, "profit": 0, "expenses": 0, "market_cap": 0, "currency": "₹"}

    metrics = extract_metrics(st.session_state["report_text"])

    # --- New Visualize Button ---
    if st.button("📊 Visualize Data (Graphs, Charts, Piecharts)"):
        # Dynamic DataFrame from extracted metrics
        df = pd.DataFrame({
            "Parameter": ["Revenue", "Profit", "Expenses", "Market Cap"],
            "Value": [metrics["revenue"], metrics["profit"], metrics["expenses"], metrics["market_cap"]]
        })
        df["Value"] = df["Value"].apply(lambda x: f"{x} {metrics['currency']} Cr" if x > 0 else "N/A")

        st.markdown("### 📉 Bar Chart")
        viz_df = df.set_index("Parameter")["Value"].str.replace(f" {metrics['currency']} Cr", "").astype(float)
        if viz_df.sum() > 0:
            st.bar_chart(viz_df)
        else:
            st.warning("⚠️ No numerical data for charts. Try a different report.")

        st.markdown("### 📈 Line Chart")
        if viz_df.sum() > 0:
            st.line_chart(viz_df)
        else:
            st.warning("⚠️ No numerical data for charts. Try a different report.")

        st.markdown("### 🥧 Pie Chart")
        positive_values = viz_df[viz_df > 0]
        if len(positive_values) > 1:  # Need at least 2 for pie
            fig, ax = plt.subplots()
            ax.pie(positive_values, labels=positive_values.index, autopct='%1.1f%%', startangle=90)
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.warning("⚠️ Insufficient data for pie chart (need at least 2 positive values).")

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
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.7,
                    max_tokens=300
                )
                summary = completion.choices[0].message.content
                st.markdown("### 📋 Summary")
                st.markdown(summary)

    # 2️⃣ Show Table
    with col2:
        if st.button("📋 Show Table"):
            # Dynamic table from metrics
            table_df = pd.DataFrame({
                "Parameter": ["Revenue", "Profit", "Expenses", "Market Cap"],
                "Value": [
                    f"{metrics['revenue']} {metrics['currency']} Cr" if metrics['revenue'] > 0 else "N/A",
                    f"{metrics['profit']} {metrics['currency']} Cr" if metrics['profit'] > 0 else "N/A",
                    f"{metrics['expenses']} {metrics['currency']} Cr" if metrics['expenses'] > 0 else "N/A",
                    f"{metrics['market_cap']} {metrics['currency']} Cr" if metrics['market_cap'] > 0 else "N/A"
                ]
            })
            st.markdown("### 🧾 Financial Table")
            st.table(table_df)