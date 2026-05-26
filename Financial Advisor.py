import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- MOBILE APP CONFIGURATION ---
st.set_page_config(page_title="Pro Wealth AI", page_icon="🏦", layout="centered")

# Custom CSS to make it look like a premium dark-mode native app
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div.stButton > button:first-child {
        background-color: #00D4B2; color: black; font-weight: bold; width: 100%; border-radius: 10px;
    }
    .metric-box {
        background-color: #1e2430; padding: 15px; border-radius: 10px; border: 1px solid #2d3748;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 Pro Wealth AI Coach")
st.markdown("*Advanced SIP Analytics & Autonomous Financial Advisor*")
st.write("---")

# --- API KEY MANAGEMENT ---
import os

# First, check if the key is hidden safely in the Streamlit Secrets panel
backend_key = st.secrets.get("GEMINI_API_KEY")

# If it's in secrets, use it automatically. If not, show a text input box on the screen.
api_key = backend_key or st.text_input("🔑 Enter Free Gemini API Key to activate AI Coach:", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.info("💡 To talk to your AI Advisor, generate a free key at aistudio.google.com and paste it above.")


# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Calculator", "🤖 Talk to AI Coach", "📑 Data Sheet"])

with tab1:
    st.subheader("📥 Investment Setup")
    
    col_a, col_b = st.columns(2)
    with col_a:
        base_sip = st.number_input("Starting Monthly SIP", min_value=1000, value=50000, step=5000)
        years = st.slider("Horizon (Years)", min_value=1, max_value=40, value=10)
    with col_b:
        annual_rate = st.slider("Expected Return (ROI %)", min_value=1.0, max_value=30.0, value=12.0, step=0.5)
        topup_amount = st.number_input("Increment/Top-Up Amount", min_value=0, value=5000, step=1000)
        
    topup_frequency = st.selectbox("Increment Frequency", ["Monthly", "Quarterly", "Mid-Year", "Annual"])

    # --- MATH CALCULATIONS ---
    freq_map = {"Monthly": 1, "Quarterly": 3, "Mid-Year": 6, "Annual": 12}
    topup_interval = freq_map.get(topup_frequency, 12)
    months = years * 12
    monthly_rate = annual_rate / 12 / 100

    current_sip = base_sip
    current_balance = 0
    total_invested = 0
    data_log = []

    for month in range(1, months + 1):
        if month > 1 and (month - 1) % topup_interval == 0:
            current_sip += topup_amount
        total_invested += current_sip
        current_balance = (current_balance + current_sip) * (1 + monthly_rate)
        profit = current_balance - total_invested
        roi = (profit / total_invested) * 100 if total_invested > 0 else 0
        
        data_log.append({
            "Month": month, "Year": round((month / 12), 2), "Monthly SIP": current_sip,
            "Total Invested": total_invested, "Future Value": current_balance,
            "Profit Gained": profit, "Absolute ROI (%)": roi
        })

    df = pd.DataFrame(data_log)

    # --- SAFETY GATE FOR INITIALIZATION ---
    if df.empty:
        st.warning("Awaiting configuration parameters to calculate metrics...")
    else:
        final = df.iloc[-1]

        # --- KPI DASHBOARD ---
        st.write("### 📈 Key Performance Indicators")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Total Capital Invested", f"${final['Total Invested']:,.2f}")
            st.metric("Absolute ROI", f"{final['Absolute ROI (%)']:.2f}%")
        with c2:
            st.metric("Maturity Wealth", f"${final['Future Value']:,.2f}")
            st.metric("Wealth Multiplier", f"{round(final['Future Value'] / final['Total Invested'], 2)}x")

        # --- GRAPH ---
        st.write("### 💹 Growth Trajectory")
        fig = px.area(df, x="Year", y=["Total Invested", "Future Value"], 
                      labels={"value": "Amount ($)", "variable": "Type"},
                      color_discrete_sequence=["#FF4B4B", "#00D4B2"])
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("🤖 Live AI Financial Consultation")
    
    if not api_key:
        st.warning("Please activate your AI Brain by putting your API key in the input box at the top.")
    elif df.empty:
        st.info("Calculate metrics on the first tab before starting an AI session.")
    else:
        st.write("The AI Coach automatically analyzes your calculator metrics.")
        
        system_instruction = """
        You are an elite, highly professional financial advisor, portfolio manager, and wealth coach. 
        You speak with precision, wisdom, and strategic depth. You analyze the user's investment metrics,
        point out the strength of their step-up increments, critique their timeline, and provide absolute 
        clarity on asset allocation, inflation protection, and wealth accumulation milestones.
        """
        
        final = df.iloc[-1]
        context = f"""
        Current Investment Profile Data:
        - Initial Monthly SIP: ${base_sip}
        - Step-Up Increment: ${topup_amount} occurring {topup_frequency}
        - Investment Horizon: {years} years
        - Expected Target ROI: {annual_rate}%
        - Calculated Total Out-of-Pocket Capital: ${final['Total Invested']:,.2f}
        - Calculated Expected Maturity Value: ${final['Future Value']:,.2f}
        - Net Profit Gained: ${final['Profit Gained']:,.2f}
        """
        
        user_question = st.text_input("Ask your Financial Coach anything:")
        
        if st.button("Consult Coach"):
            if user_question:
                with st.spinner("Analyzing market dynamics and portfolio metrics..."):
                    try:
                        model = genai.GenerativeModel('models/gemini-1.5-flash')
                        full_prompt = f"{system_instruction}\n\nContext on User's Math:\n{context}\n\nUser Question: {user_question}"
                        response = model.generate_content(full_prompt)
                        st.markdown(f"### 💡 Coach Response:\n{response.text}")
                    except Exception as e:
                        st.error(f"Error communicating with AI: {e}")

with tab3:
    st.subheader("📑 Audit Statement")
    if df.empty:
        st.info("No statement entries available.")
    else:
        st.dataframe(df.style.format({
            "Monthly SIP": "${:,.2f}", "Total Invested": "${:,.2f}", 
            "Future Value": "${:,.2f}", "Profit Gained": "${:,.2f}", "Absolute ROI (%)": "{:.2f}%"
        }))
