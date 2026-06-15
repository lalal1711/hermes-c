import requests
import pandas as pd

def analyze_crypto_market(symbol: str, timeframe: str = '1h', limit: int = 50):
    """
    通过 Bitget V2 API 获取 K 线数据并进行基础技术分析，将结果返回给 Hermes
    """
    # Bitget V2 现货 K 线 API
    url = "https://api.bitget.com/api/v2/spot/market/candles"
    
    params = {
        "symbol": symbol.upper(),
        "granularity": timeframe,
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("code") != "00000":
            return {"error": f"API 错误: {data.get('msg')}"}
            
        candles = data.get("data", [])
        if not candles:
            return {"error": "未找到该交易对的数据，请检查 symbol (如 BTCUSDT)"}
            
        # Bitget 返回的数据格式: [timestamp, open, high, low, close, base_volume, quote_volume]
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "base_vol", "quote_vol"])
        
        # 数据类型转换
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "base_vol": float})
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")
        
        # 按时间升序排列（确保时间从旧到新，这样计算均线才准确）
        df = df.sort_values(by="timestamp", ascending=True).reset_index(drop=True)
        
        # 核心数据计算
        current_price = df["close"].iloc[-1]
        highest_price = df["high"].max()
        lowest_price = df["low"].min()
        
        # 区间整体涨跌幅
        start_price = df["open"].iloc[0]
        period_change = ((current_price - start_price) / start_price) * 100
        
        # 移动平均线 (MA) - 计算 MA7 和 MA20
        df["MA_7"] = df["close"].rolling(window=7).mean()
        df["MA_20"] = df["close"].rolling(window=20).mean()
        
        ma_7 = df["MA_7"].iloc[-1]
        ma_20 = df["MA_20"].iloc[-1]
        
        # 组装返回给 Hermes 的纯数据字典
        analysis_result = {
            "exchange": "Bitget",
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "data_points": len(df),
            "current_price": current_price,
            "period_highest": highest_price,
            "period_lowest": lowest_price,
            "period_change_percent": round(period_change, 2),
            "indicators": {
                "MA_7": round(ma_7, 4) if not pd.isna(ma_7) else None,
                "MA_20": round(ma_20, 4) if not pd.isna(ma_20) else None
            },
            "trend_signal": "Bullish (看涨)" if period_change > 0 else "Bearish (看跌)"
        }
        
        return analysis_result
        
    except Exception as e:
        return {"error": f"执行分析时发生系统错误: {str(e)}"}

# 测试代码
# print(analyze_crypto_market("BTCUSDT", "1h", 50))