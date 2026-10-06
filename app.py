import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import io

st.set_page_config(page_title="Indian Stock Ultimate Market Scanner", layout="wide")
st.title("🇮🇳 Indian Stock Market Complete Segment Scanner")
st.write("Scan Large, Mid, Small, or Micro-cap indices to identify stocks meeting your 5-year profit thesis framework.")

# Helper function to dynamically map and clean ticker endpoints
@st.cache_data
def load_index_tickers(index_name):
    base_url = "https://githubusercontent.com"
    
    urls = {
        "Nifty 50 (Mega Caps)": f"{base_url}NIFTY50.csv",
        "Nifty Midcap 150": f"{base_url}NIFTY_MIDCAP_150.csv",
        "Nifty Smallcap 250": f"{base_url}NIFTY_SMALLCAP_250.csv",
        "Nifty Microcap 250 (Micro Caps)": f"{base_url}NIFTY_MICROCAP_250.csv"
    }
    
    try:
        url = urls[index_name]
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            df = pd.read_csv(io.StringIO(response.read().decode('utf-8')))
            
        # Dynamically search for the text column containing symbol data
        symbol_col = [col for col in df.columns if 'Symbol' in col or 'symbol' in col or 'SYMBOL' in col]
        if symbol_col:
            tickers = [str(sym).strip() + ".NS" for sym in df[symbol_col[0]].dropna().unique()]
            return tickers
    except Exception:
        pass
        
    # Reliable backup fallbacks if GitHub raw lists hit temporary latency
    fallbacks = {
        "Nifty 50 (Mega Caps)": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"],
        "Nifty Midcap 150": ["TATAMOTORS.NS", "FEDERALBNK.NS", "VOLTAS.NS", "PAGEIND.NS"],
        "Nifty Smallcap 250": ["SUZLON.NS", "RBLBANK.NS", "CEAT.NS", "CDSL.NS"],
        "Nifty Microcap 250 (Micro Caps)": ["INFIBEAM.NS", "DEN.NS", "SURYODAY.NS"]
    }
    return fallbacks.get(index_name, ["RELIANCE.NS"])

# Refined layout UI selector
selected_index = st.selectbox(
    "🎯 Choose the specific stock market layer to sweep:",
    [
        "Nifty 50 (Mega Caps)", 
        "Nifty Midcap 150", 
        "Nifty Smallcap 250", 
        "Nifty Microcap 250 (Micro Caps)"
    ]
)

tickers_to_scan = load_index_tickers(selected_index)
st.info(f"📋 Loaded {len(tickers_to_scan)} companies inside the {selected_index} segment.")

# Added a batch slider limit so users don't get banned by Yahoo Finance if running massive micro-cap sets
max_scan = st.slider("⚙️ Limit scan batch size (Recommended for quick testing):", 5, len(tickers_to_scan), min(50, len(tickers_to_scan)))

if st.button("🚀 Run Live Engine Sweep", type="primary"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    scan_pool = tickers_to_scan[:max_scan]
    
    for idx, ticker_symbol in enumerate(scan_pool):
        status_text.text(f"Analyzing {ticker_symbol} ({idx + 1}/{len(scan_pool)})...")
        progress_bar.progress((idx + 1) / len(scan_pool))
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            market_cap_inr = info.get("marketCap", 0)
            if market_cap_inr <= 0:
                continue
            market_cap_crores = market_cap_inr / 10_000_000
            
            financials = ticker.financials
            if "Net Income" not in financials.index:
                continue
                
            recent_net_income = financials.loc["Net Income"].iloc[0]
            recent_profit_crores = recent_net_income / 10_000_000
            
            # Use dynamic growth parameters or use 10% base projection for smaller caps
            growth_rate = info.get("earningsGrowth", 0.10)
            if growth_rate is None or growth_rate <= 0:
                growth_rate = 0.10
                
            projected_profits = []
            current_baseline = recent_profit_crores
            for year in range(1, 6):
                current_baseline = current_baseline * (1 + growth_rate)
                projected_profits.append(current_baseline)
                
            total_5yr_profit_crores = sum(projected_profits)
            passed = total_5yr_profit_crores >= market_cap_crores
            
            results.append({
                "Ticker": ticker_symbol.replace(".NS", ""),
                "Market Cap (Cr)": round(market_cap_crores, 2),
                "Current Annual Profit (Cr)": round(recent_profit_crores, 2),
                "Est. Growth Rate": f"{round(growth_rate * 100, 2)}%",
                "Projected 5-Yr Profit (Cr)": round(total_5yr_profit_crores, 2),
                "Thesis Match": "✅ PASS" if passed else "❌ FAIL"
            })
        except Exception:
            continue
            
    status_text.text("Sweep completed successfully!")
    
    if results:
        df = pd.DataFrame(results)
        passed_df = df[df["Thesis Match"] == "✅ PASS"]
        
        if not passed_df.empty:
            st.success(f"🎉 Found {len(passed_df)} stocks matching your exact framework criteria!")
            st.dataframe(passed_df, use_container_width=True)
            
            csv = passed_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Matches to CSV", data=csv, file_name="cap_thesis_matches.csv", mime="text/csv")
        else:
            st.warning("No companies in this checked batch satisfied the conditions today.")
            
        st.write("Full Processing Log Table View:")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Engine failed to compute valid structural outputs.")
