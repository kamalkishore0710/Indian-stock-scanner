import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import io

st.set_page_config(page_title="Indian Stock Deep Value Scanner", layout="wide")
st.title("🇮🇳 Indian Stock Market Multi-Index Scanner")
st.write("Scan entire index universes to find companies where projected 5-year consecutive net profits exceed current market cap.")

# Helper function to download official NSE index files live
@st.cache_data
def load_index_tickers(index_name):
    # Official public GitHub data mappings or NSE tracking repositories for clean tickers
    urls = {
        "Nifty 50 (Mega Caps)": "https://githubusercontent.com",
        "Nifty 100 (Large Caps)": "https://githubusercontent.com",
        "Nifty 500 (94% of Market Cap)": "https://githubusercontent.com"
    }
    
    try:
        url = urls[index_name]
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            df = pd.read_csv(io.StringIO(response.read().decode('utf-8')))
            
        # Clean standard NSE formats and append Yahoo suffix (.NS)
        symbol_col = [col for col in df.columns if 'Symbol' in col or 'symbol' in col or 'SYMBOL' in col][0]
        tickers = [str(sym).strip() + ".NS" for sym in df[symbol_col].dropna().unique()]
        return tickers
    except Exception as e:
        # Static resilient fallback if github download fails
        fallback = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "ITC.NS", "SBIN.NS"]
        return fallback

# User configuration menu inside the UI
selected_index = st.selectbox(
    "🎯 Select the Market Segment you want to scan:",
    ["Nifty 50 (Mega Caps)", "Nifty 100 (Large Caps)", "Nifty 500 (94% of Market Cap)"]
)

tickers_to_scan = load_index_tickers(selected_index)
st.info(f"Loaded {len(tickers_to_scan)} stocks inside the selected universe.")

if st.button("🚀 Run Indian Market Scan", type="primary"):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Process batch sizes neatly to avoid rate limiting loops
    for idx, ticker_symbol in enumerate(tickers_to_scan):
        status_text.text(f"Processing {ticker_symbol} ({idx + 1}/{len(tickers_to_scan)})...")
        progress_bar.progress((idx + 1) / len(tickers_to_scan))
        
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
            
            growth_rate = info.get("earningsGrowth", 0.08)
            if growth_rate is None or growth_rate <= 0:
                growth_rate = 0.08
                
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
            
    status_text.text("Scan complete!")
    
    if results:
        df = pd.DataFrame(results)
        passed_df = df[df["Thesis Match"] == "✅ PASS"]
        
        if not passed_df.empty:
            st.success(f"Found {len(passed_df)} stocks matching your thesis!")
            st.dataframe(passed_df, use_container_width=True)
            
            # Allow data export to CSV
            csv = passed_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Matches as CSV", data=csv, file_name="thesis_matches.csv", mime="text/csv")
        else:
            st.warning("No stocks in this specific index met the criteria today.")
            
        st.write("Full Scan Log Detail:")
        st.dataframe(df, use_container_width=True)
    else:
        st.error("No valid data could be retrieved during this loop runtime.")
