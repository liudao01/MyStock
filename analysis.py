"""
股票指标 & 背离算法
"""
import akshare as ak
import pandas as pd
import numpy as np
import ta
from datetime import datetime


def normalize_symbol(code: str) -> str:
    code = code.strip()
    if code.startswith("6"):
        return "sh" + code
    elif code.startswith(("0", "3")):
        return "sz" + code
    else:
        return code


def compute_enhanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_index()
    # MACD
    df["macd_dif"]   = ta.trend.macd_diff(df["close"])
    df["macd_signal"]= ta.trend.macd_signal(df["close"])
    df["macd"]       = df["macd_dif"] - df["macd_signal"]
    # KDJ
    kdj = ta.momentum.StochasticOscillator(
        high=df["high"], low=df["low"], close=df["close"], window=9, smooth_window=3
    )
    df["kdj_k"] = kdj.stoch()
    df["kdj_d"] = kdj.stoch_signal()
    df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]
    # RSI & MA
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    df["ma5"]  = df["close"].rolling(5).mean()
    df["ma10"] = df["close"].rolling(10).mean()
    df["ma20"] = df["close"].rolling(20).mean()
    # 量均线
    df["volume_ma5"]  = df["volume"].rolling(5).mean()
    df["volume_ma10"] = df["volume"].rolling(10).mean()
    return df


def find_robust_lows(prices, dates, window=10, min_trading_days=10):
    lows = []
    for i in range(window, len(prices) - window):
        left_min  = min(prices[i - window : i])
        right_min = min(prices[i + 1 : i + window + 1])
        if prices[i] <= left_min and prices[i] <= right_min:
            if lows:
                days_diff = (dates.iloc[i] - dates.iloc[lows[-1]]).days
                if days_diff >= min_trading_days:
                    lows.append(i)
            else:
                lows.append(i)
    return lows


def comprehensive_divergence_analysis(df: pd.DataFrame):
    df_reset = df.reset_index()
    dates = pd.to_datetime(df_reset["date"]) if "date" in df_reset.columns else pd.to_datetime(df_reset.index)
    price_lows = df_reset["close"].values
    macd_vals  = df_reset["macd"].values
    dif_vals   = df_reset["macd_dif"].values
    rsi_vals   = df_reset["rsi"].values
    volume_vals= df_reset["volume"].values

    low_indices = find_robust_lows(price_lows, dates, window=8, min_trading_days=10)
    if len(low_indices) < 2:
        return None
    idx1, idx2 = low_indices[-2], low_indices[-1]
    if price_lows[idx2] >= price_lows[idx1]:
        return None

    signals, conf = [], []
    macd_cnt = 0
    # 1 2 MACD
    if macd_vals[idx2] > macd_vals[idx1]:
        signals.append("MACD柱状线背离"); conf.append(0.3); macd_cnt += 1
    if dif_vals[idx2] > dif_vals[idx1]:
        signals.append("DIF线背离");     conf.append(0.3); macd_cnt += 1
    # 3 RSI
    if rsi_vals[idx2] > rsi_vals[idx1]:
        signals.append("RSI背离");       conf.append(0.2)
    # 4 量
    vol_ratio = volume_vals[idx2] / volume_vals[idx1]
    if vol_ratio < 1.5:
        signals.append("成交量配合");    conf.append(0.1)
    # 5 跌幅
    price_drop = (price_lows[idx1] - price_lows[idx2]) / price_lows[idx1]
    if price_drop > 0.05:
        signals.append("价格有效新低");  conf.append(0.1)

    if len(signals) < 2:
        return None

    # 分级
    if macd_cnt == 2:
        level, confidence = "强烈背离", min(sum(conf), 0.95)
    elif macd_cnt == 1:
        level, confidence = "小背离",   min(sum(conf) * 0.7, 0.7)
    else:
        level, confidence = "背离",     min(sum(conf), 0.9)

    return {
        "date1": dates.iloc[idx1],
        "date2": dates.iloc[idx2],
        "price1": price_lows[idx1],
        "price2": price_lows[idx2],
        "signals": signals,
        "confidence": confidence,
        "details": f"{dates.iloc[idx1].strftime('%m-%d')} {price_lows[idx1]:.2f} → "
                   f"{dates.iloc[idx2].strftime('%m-%d')} {price_lows[idx2]:.2f}",
        "level": level
    }


def analyze_trend(df: pd.DataFrame) -> str:
    if len(df) < 20:
        return "数据不足"
    recent = df.tail(20)
    cur = recent.iloc[-1]
    score = (cur["close"] > cur["ma5"]) + (cur["close"] > cur["ma10"]) + (cur["close"] > cur["ma20"])
    return "短期上升趋势" if score >= 2 else "震荡趋势" if score == 1 else "下跌趋势"

def get_stock_name(code: str) -> str:
    """输入 000001/sz000001 返回股票简称，失败返回原代码"""
    try:
        return ak.stock_individual_info_em(symbol=code).loc[1, "value"]
    except Exception:
        return code
    
def generate_trading_advice(div, df: pd.DataFrame) -> str:
    if not div:
        return "暂无明确交易信号"
    level = div.get("level", "背离")
    advice = []
    if level == "强烈背离":
        advice.append("🔔 强烈关注：MACD双信号确认")
    elif level == "小背离":
        advice.append("⚠️ 关注：MACD单信号背离")
    else:
        advice.append("ℹ️ 技术信号：保持观察")

    cur_dif, cur_dea = df.iloc[-1]["macd_dif"], df.iloc[-1]["macd_signal"]
    if cur_dif > cur_dea:
        advice.append("MACD已金叉，趋势转强")
    else:
        advice.append("等待MACD金叉确认")
    advice.append("设止损在近期低点下方3-5%")
    return " | ".join(advice)