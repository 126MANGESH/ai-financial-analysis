from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import os
import re
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("❌ GROQ_API_KEY not found in .env file")

# Initialize Flask app
app = Flask(__name__)
client = Groq(api_key=api_key)

# ==================== PROMPT LIBRARY ====================
PROMPTS = {
    "business_model": """
Explain the business model of {company_name}.
Describe its main revenue streams, customer segments, value proposition, and cost structure.
Summarize in 4-5 bullet points.
    """,
    "management_commentary": """
Summarize the recent management commentary for {company_name}.
Highlight key themes such as business outlook, challenges, opportunities, and strategic decisions.
Keep it concise and actionable.
    """,
    "red_flags": """
Identify and explain potential red flags for {company_name}.
Include points such as:
- Governance or regulatory issues
- Declining margins or rising debt
- Frequent leadership changes
- Auditor resignations or lawsuits
Provide a short summary.
    """,
    "key_products": """
Create a summary of key products or services offered by {company_name}.
Include Product/Service names, segments, and growth trends.
    """,
    "evolution": """
Describe the evolution of {company_name} over the last 3 years.
Cover:
- Business expansion or restructuring
- Financial performance trends
- New product launches
- Mergers, acquisitions, or partnerships
Present in a concise 3-year timeline format.
    """,
    "stock_performance": """
Based on recent financial data and management commentary, analyze how the stock of {company_name} is expected to perform in the next 6–12 months.
Include technical and fundamental insights where possible.
Summarize risks and catalysts.
    """,
    "growth_outlook": """
Project the growth outlook for {company_name} over the next 3 years.
Include potential drivers (sector growth, policy, expansion) and risks.
Summarize with key metrics like Revenue CAGR and ROE trends.
    """,
    "guidance_vs_delivery": """
Analyze management's past guidance vs actual delivery for {company_name}.
Highlight whether management has been consistent or overpromising.
    """
}

def select_prompt(query, company_name):
    """Auto-select appropriate prompt based on query"""
    query_lower = query.lower()
    
    if "business model" in query_lower:
        prompt_type = "business_model"
    elif "management" in query_lower and "commentary" in query_lower:
        prompt_type = "management_commentary"
    elif "red flag" in query_lower:
        prompt_type = "red_flags"
    elif "product" in query_lower or "service" in query_lower:
        prompt_type = "key_products"
    elif "evolution" in query_lower:
        prompt_type = "evolution"
    elif "stock" in query_lower or "performance" in query_lower:
        prompt_type = "stock_performance"
    elif "growth" in query_lower or "outlook" in query_lower:
        prompt_type = "growth_outlook"
    elif "guidance" in query_lower:
        prompt_type = "guidance_vs_delivery"
    else:
        return query  # Use raw query for general analysis
    
    return PROMPTS[prompt_type].format(company_name=company_name)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Main API endpoint for financial analysis
    Expects JSON: {
        "company_name": str,
        "query": str,
        "model": str (smart or expert)
    }
    """
    try:
        # Get request data
        data = request.json
        company_name = data.get('company_name', '').strip()
        query = data.get('query', '').strip()
        model = data.get('model', 'smart')
        
        # Validation
        if not company_name:
            return jsonify({'error': 'Company name is required'}), 400
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Select and format prompt
        prompt = select_prompt(query, company_name)
        
        # Call Groq API
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7 if model == 'smart' else 0.5,
            max_tokens=1024
        )
        
        # Extract response
        response_text = completion.choices[0].message.content
        
        return jsonify({
            'success': True,
            'response': response_text,
            'company': company_name,
            'model_used': model
        }), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'api_key_configured': bool(api_key)}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)