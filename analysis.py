"""
股票指标 & 背离算法 - 优化版
专注于近期150个交易日的背离检测
"""
import akshare as ak
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta


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


def find_recent_lows(df, lookback_days=150, min_days_between_lows=10):
    """
    在最近指定天数内寻找局部低点
    优化：专注于近期数据，避免找到太早的背离
    """
    # 确保数据按日期排序
    df = df.sort_index().tail(lookback_days)
    
    # 重置索引以便按位置访问
    df_reset = df.reset_index()
    dates = pd.to_datetime(df_reset["date"]) if "date" in df_reset.columns else pd.to_datetime(df_reset.index)
    prices = df_reset["close"].values
    
    # 寻找局部低点
    lows = []
    window = 5  # 局部低点检测窗口
    
    for i in range(window, len(prices) - window):
        # 检查是否是局部低点
        left_min = min(prices[i-window:i])
        right_min = min(prices[i+1:i+window+1])
        
        if prices[i] <= left_min and prices[i] <= right_min:
            # 检查时间间隔
            if lows:
                days_diff = (dates.iloc[i] - dates.iloc[lows[-1]]).days
                if days_diff >= min_days_between_lows:
                    lows.append(i)
            else:
                lows.append(i)
    
    return lows, df_reset, dates


def comprehensive_divergence_analysis(df: pd.DataFrame):
    """
    专注于近期150个交易日的背离分析
    """
    # 收集计算过程信息
    calculation_steps = []
    calculation_steps.append(f"🔍 在最近150个交易日内寻找背离信号")
    
    # 寻找近期低点
    low_indices, df_reset, dates = find_recent_lows(df, lookback_days=150, min_days_between_lows=10)
    
    if len(low_indices) < 2:
        calculation_steps.append(f"❌ 未找到足够的近期局部低点 (找到{len(low_indices)}个)")
        return None, "\n".join(calculation_steps)
    
    calculation_steps.append(f"✅ 找到{len(low_indices)}个近期局部低点")
    
    # 获取指标数据
    price_lows = df_reset["close"].values
    macd_vals  = df_reset["macd"].values
    dif_vals   = df_reset["macd_dif"].values
    rsi_vals   = df_reset["rsi"].values
    volume_vals= df_reset["volume"].values
    
    # 只关注最近的两个低点
    idx1, idx2 = low_indices[-2], low_indices[-1]
    
    calculation_steps.append(f"📅 分析最近的两个低点:")
    calculation_steps.append(f"   低点A: 日期{dates.iloc[idx1].strftime('%Y-%m-%d')}, 价格{price_lows[idx1]:.2f}")
    calculation_steps.append(f"   低点B: 日期{dates.iloc[idx2].strftime('%Y-%m-%d')}, 价格{price_lows[idx2]:.2f}")
    calculation_steps.append(f"   时间间隔: {(dates.iloc[idx2] - dates.iloc[idx1]).days}天")
    
    # 检查价格是否创新低
    if price_lows[idx2] >= price_lows[idx1]:
        calculation_steps.append(f"❌ 价格未创新低: {price_lows[idx2]:.2f} >= {price_lows[idx1]:.2f}")
        return None, "\n".join(calculation_steps)

    calculation_steps.append(f"✅ 价格创新低: {price_lows[idx2]:.2f} < {price_lows[idx1]:.2f} (跌幅:{(price_lows[idx1]-price_lows[idx2])/price_lows[idx1]:.2%})")

    # 检测背离信号
    signals, conf = [], []
    macd_cnt = 0
    calculation_steps.append(f"\n📊 背离信号检测:")
    
    # 1. MACD柱状线背离
    if macd_vals[idx2] > macd_vals[idx1]:
        signals.append("MACD柱状线背离"); conf.append(0.3); macd_cnt += 1
        calculation_steps.append(f"   ✅ MACD柱状线: {macd_vals[idx2]:.4f} > {macd_vals[idx1]:.4f}")
    else:
        calculation_steps.append(f"   ❌ MACD柱状线: {macd_vals[idx2]:.4f} <= {macd_vals[idx1]:.4f}")
        
    # 2. DIF线背离  
    if dif_vals[idx2] > dif_vals[idx1]:
        signals.append("DIF线背离");     conf.append(0.3); macd_cnt += 1
        calculation_steps.append(f"   ✅ DIF线: {dif_vals[idx2]:.4f} > {dif_vals[idx1]:.4f}")
    else:
        calculation_steps.append(f"   ❌ DIF线: {dif_vals[idx2]:.4f} <= {dif_vals[idx1]:.4f}")
        
    # 3. RSI背离
    if rsi_vals[idx2] > rsi_vals[idx1]:
        signals.append("RSI背离");       conf.append(0.2)
        calculation_steps.append(f"   ✅ RSI: {rsi_vals[idx2]:.1f} > {rsi_vals[idx1]:.1f}")
    else:
        calculation_steps.append(f"   ❌ RSI: {rsi_vals[idx2]:.1f} <= {rsi_vals[idx1]:.1f}")
        
    # 4. 成交量确认
    vol_ratio = volume_vals[idx2] / volume_vals[idx1] if volume_vals[idx1] > 0 else 1
    if vol_ratio < 1.5:
        signals.append("成交量配合");    conf.append(0.1)
        calculation_steps.append(f"   ✅ 成交量: 比率{vol_ratio:.2f} < 1.5")
    else:
        calculation_steps.append(f"   ❌ 成交量: 比率{vol_ratio:.2f} >= 1.5")
        
    # 5. 有效跌幅确认
    price_drop = (price_lows[idx1] - price_lows[idx2]) / price_lows[idx1]
    if price_drop > 0.03:  # 调整为3%的跌幅要求，更适合近期分析
        signals.append("价格有效新低");  conf.append(0.1)
        calculation_steps.append(f"   ✅ 价格跌幅: {price_drop:.2%} > 3%")
    else:
        calculation_steps.append(f"   ❌ 价格跌幅: {price_drop:.2%} <= 3%")

    calculation_steps.append(f"\n📈 信号统计: 共{len(signals)}个信号, MACD相关信号{macd_cnt}个")
    calculation_steps.append(f"   具体信号: {', '.join(signals)}")

    # 检查是否满足最低信号要求
    if len(signals) < 2:
        calculation_steps.append(f"❌ 信号不足: 需要至少2个信号, 当前只有{len(signals)}个")
        return None, "\n".join(calculation_steps)

    # 分级判定
    if macd_cnt == 2:
        level, confidence = "强烈背离", min(sum(conf), 0.95)
        calculation_steps.append(f"🎯 级别判定: {level} (MACD双信号确认)")
    elif macd_cnt == 1:
        level, confidence = "小背离",   min(sum(conf) * 0.8, 0.8)  # 提高小背离的置信度
        calculation_steps.append(f"🎯 级别判定: {level} (MACD单信号)")
    else:
        level, confidence = "普通背离", min(sum(conf) * 0.6, 0.7)  # 降低无MACD信号的置信度
        calculation_steps.append(f"🎯 级别判定: {level} (无MACD信号)")

    calculation_steps.append(f"📊 最终置信度: {confidence:.1%}")

    # 返回结果
    result = {
        "date1": dates.iloc[idx1],
        "date2": dates.iloc[idx2],
        "price1": price_lows[idx1],
        "price2": price_lows[idx2],
        "macd1": macd_vals[idx1],
        "macd2": macd_vals[idx2],
        "dif1": dif_vals[idx1],
        "dif2": dif_vals[idx2],
        "rsi1": rsi_vals[idx1],
        "rsi2": rsi_vals[idx2],
        "volume1": volume_vals[idx1],
        "volume2": volume_vals[idx2],
        "signals": signals,
        "confidence": confidence,
        "details": f"{dates.iloc[idx1].strftime('%m-%d')} {price_lows[idx1]:.2f} → {dates.iloc[idx2].strftime('%m-%d')} {price_lows[idx2]:.2f}",
        "level": level,
        "calculation_steps": "\n".join(calculation_steps),
        "time_span": f"{(dates.iloc[idx2] - dates.iloc[idx1]).days}天"  # 新增时间跨度信息
    }
    
    return result, None


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