import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Indian Stock Deep Value Scanner", layout="wide")
st.title("🇮🇳 Indian Stock Market 5-Year Profit Scanner")
st.write("Scan Indian equities to find companies where projected 5-year consecutive net profits exceed their current market cap.")

# Start with a curated basket of major Indian companies for speed and reliability
TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS",
    "LTIM.NS", "WIPRO.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ONGC.NS", "COALINDIA.NS", "NTPC.NS", "IOC.NS", "GAIL.NS",
    "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "BPCL.NS"
]

if st.button("🚀 Run Indian Market Scan", type="primary"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, ticker_symbol in enumerate(TICKERS):
        status_text.text(f"Scanning {ticker_symbol} ({idx + 1}/{len(TICKERS)})...")
        progress_bar.progress((idx + 1) / len(TICKERS))
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # Fetch Market Capitalization (Convert to INR Crores for local readability)
            market_cap_inr = info.get("marketCap", 0)
            if market_cap_inr <= 0:
                continue
            market_cap_crores = market_cap_inr / 10_000_000
            
            # Fetch Income Statement for historical/current profit baseline
            financials = ticker.financials
            if "Net Income" not in financials.index:
                continue
                
            # Use the most recent full-year net income
            recent_net_income = financials.loc["Net Income"].iloc[0]
            recent_profit_crores = recent_net_income / 10_000_000
            
            # Growth assumption: Use consensus if available, fallback to conservative 8%
            growth_rate = info.get("earningsGrowth", 0.08)
            if growth_rate is None or growth_rate <= 0:
                growth_rate = 0.08
                
            # Extrapolate 5 years of future profit based on current baseline and growth
            projected_profits = []
            current_baseline = recent_profit_crores
            for year in range(1, 6):
                current_baseline = current_baseline * (1 + growth_rate)
                projected_profits.append(current_baseline)
                
            total_5yr_profit_crores = sum(projected_profits)
            
            # Check the thesis constraint
            passed = total_5yr_profit_crores >= market_cap_crores
            
            results.append({
                "Ticker": ticker_symbol.replace(".NS", ""),
                "Market Cap (Cr)": round(market_cap_crores, 2),
                "Current Annual Profit (Cr)": round(recent_profit_crores, 2),
                "Est. Growth Rate": f"{round(growth_rate * 100, 2)}%",
                "Projected 5-Yr Profit (Cr)": round(total_5yr_profit_crores, 2),
                "Thesis Match": "✅ PASS" if passed else "❌ FAIL"
            })
        except Exception as e:
            continue
            
    status_text.text("Scan complete!")
    df = pd.DataFrame(results)
    
    # Filter out only the stocks that pass your rule
    passed_df = df[df["ThesisMatch"] == "✅ PASS"] if "ThesisMatch" in df.columns else df[df["Thesis Match"] == "✅ PASS"]
    
    if not passed_df.empty:
        st.success(f"Found {len(passed_df)} stocks matching your thesis!")
        st.dataframe(passed_df, use_container_width=True)
    else:
        st.warning("No stocks in this batch met the criteria. Try adding more mid-caps or cyclical tickers next!")
        st.write("All scanned results below:")
        st.dataframe(df, use_container_width=True)
