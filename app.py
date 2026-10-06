import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import io

st.set_page_config(page_title="Indian Stock Advanced Thesis Scanner", layout="wide")
st.title("🇮🇳 Indian Stock Market Complete Segment Scanner")
st.write("Find companies where **Projected 5-Yr Net Profits ≥ Current Market Cap** AND **PEG Ratio < 1.0** (Undervalued Growth).")

# Helper function to dynamically map, download, and clean index components
@st.cache_data
def load_index_tickers(index_name):
    base_url = "https://githubusercontent.com"
    
    urls = {
        "Nifty 50 (Mega Caps)": f"{base_url}NIFTY50.csv",
        "Nifty 500 (Comprehensive Market)": f"{base_url}NIFTY500.csv",
        "Nifty Midcap 150": f"{base_url}NIFTY_MIDCAP_150.csv",
        "Nifty Smallcap 250": f"{base_url}NIFTY_SMALLCAP_250.csv",
        "Nifty Microcap 250 (Micro Caps)": f"{base_url}NIFTY_MICROCAP_250.csv"
    }
    
    try:
        url = urls[index_name]
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            df = pd.read_csv(io.StringIO(response.read().decode('utf-8')))
            
        symbol_col = [col for col in df.columns if 'Symbol' in col or 'symbol' in col or 'SYMBOL' in col]
        if symbol_col:
            tickers = [str(sym).strip() + ".NS" for sym in df[symbol_col].dropna().unique()]
            return tickers
    except Exception:
        pass
        
    fallbacks = {
        "Nifty 50 (Mega Caps)": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS"],
        "Nifty 500 (Comprehensive Market)": ["RELIANCE.NS", "TCS.NS", "SUZLON.NS"],
        "Nifty Midcap 150": ["TATAMOTORS.NS", "FEDERALBNK.NS"],
        "Nifty Smallcap 250": ["SUZLON.NS", "CDSL.NS"],
        "Nifty Microcap 250 (Micro Caps)": ["INFIBEAM.NS", "DEN.NS"]
    }
    return fallbacks.get(index_name, ["RELIANCE.NS"])

# Streamlined Selection Interface
selected_index = st.selectbox(
    "🎯 Select the exact market segment you want to analyze:",
    [
        "Nifty 50 (Mega Caps)",
        "Nifty 500 (Comprehensive Market)",
        "Nifty Midcap 150", 
        "Nifty Smallcap 250", 
        "Nifty Microcap 250 (Micro Caps)"
    ]
)

tickers_to_scan = load_index_tickers(selected_index)
st.info(f"📋 Loaded {len(tickers_to_scan)} companies matching your selection.")

# Workload regulator slider
max_scan = st.slider("⚙️ Limit scan batch size (Recommended for quick testing):", 5, len(tickers_to_scan), min(50, len(tickers_to_scan)))

if st.button("🚀 Run Live Engine Sweep", type="primary"):
    results = []
    errors_logged = 0
    progress_bar = st.progress(0)
    st_text = st.empty()
    
    scan_pool = tickers_to_scan[:max_scan]
    
    for idx, ticker_symbol in enumerate(scan_pool):
        st_text.text(f"Analyzing {ticker_symbol} ({idx + 1}/{len(scan_pool)})...")
        progress_bar.progress((idx + 1) / len(scan_pool))
        
        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # 1. Fetch Market Capitalization Safely
            market_cap_inr = info.get("marketCap", 0) or 0
            if market_cap_inr <= 0:
                continue
            market_cap_crores = market_cap_inr / 10_000_000
            
            # 2. Extract PEG Ratio Safely (Fallback to None if missing)
            peg_ratio = info.get("pegRatio", None)
            if peg_ratio is not None:
                peg_ratio = float(peg_ratio)
            
            # 3. Pull Financial Statement Framework Safely
            financials = ticker.financials
            net_income_row = None
            
            if financials is not None and not financials.empty:
                for target_label in ["Net Income", "NetIncome", "netIncome"]:
                    if target_label in financials.index:
                        net_income_row = financials.loc[target_label]
                        break
            
            if net_income_row is None or len(net_income_row) == 0:
                errors_logged += 1
                continue
                
            recent_net_income = net_income_row.iloc[0]
            if pd.isna(recent_net_income) or recent_net_income is None:
                continue
                
            recent_profit_crores = float(recent_net_income) / 10_000_000
            
            # 4. Growth calculations 
            growth_rate = info.get("earningsGrowth", 0.10)
            if growth_rate is None or not isinstance(growth_rate, (int, float)) or growth_rate <= 0:
                growth_rate = 0.10
                
            projected_profits = []
            current_baseline = recent_profit_crores
            for year in range(1, 6):
                current_baseline = current_baseline * (1 + growth_rate)
                projected_profits.append(current_baseline)
                
            total_5yr_profit_crores = sum(projected_profits)
            
            # 5. Evaluate Combined Dual-Thesis Rules
            profit_thesis_passed = total_5yr_profit_crores >= market_cap_crores
            peg_thesis_passed = (peg_ratio is not None) and (peg_ratio < 1.0)
            
            final_pass = profit_thesis_passed and peg_thesis_passed
            
            results.append({
                "Ticker": ticker_symbol.replace(".NS", ""),
                "Market Cap (Cr)": round(market_cap_crores, 2),
                "Current Annual Profit (Cr)": round(recent_profit_crores, 2),
                "Est. Growth Rate": f"{round(growth_rate * 100, 2)}%",
                "Projected 5-Yr Profit (Cr)": round(total_5yr_profit_crores, 2),
                "PEG Ratio": round(peg_ratio, 2) if peg_ratio is not None else "N/A",
                "Thesis Match": "✅ PASS" if final_pass else "❌ FAIL"
            })
        except Exception:
            errors_logged += 1
            continue
            
    st_text.text("Sweep completed!")
    
    if results:
        df = pd.DataFrame(results)
        passed_df = df[df["Thesis Match"] == "✅ PASS"]
        
        if not passed_df.empty:
            st.success(f"🎉 Found {len(passed_df)} high-quality undervalued growth stocks!")
            st.dataframe(passed_df, use_container_width=True)
            
            csv = passed_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Dynamic Watchlist to CSV", data=csv, file_name="peg_thesis_matches.csv", mime="text/csv")
        else:
            st.warning("No companies in this checked batch satisfied both your 5-year profit goal AND the PEG < 1 criterion.")
            
        st.write("Full Processing Log Table View:")
        st.dataframe(df, use_container_width=True)
    else:
        st.error(f"Engine failed to process clean metrics. (Skipped {errors_logged} rows due to lack of API data structures)")
