"""
Streamlit 前端
"""
import streamlit as st
from analysis import *
from storage import *

st.set_page_config(page_title="股票底背离检测", layout="centered")
st.title("📈 股票技术分析 · 底背离检测")

# ---------------- 自选股管理 ----------------
st.markdown("---")
st.header("📁 自选股管理")
with st.expander("增删改自选股", expanded=True):
    col_a, col_b = st.columns([3, 1])
    with col_a:
        new_code = st.text_input("输入 6 位代码", max_chars=6, key="add_code")
    with col_b:
        st.write("")  # 占位
        if st.button("加入自选", type="primary"):
            if new_code.isdigit() and len(new_code) == 6:
                if add_stock(new_code):
                    st.success(f"{new_code} 已加入")
                    st.rerun()
                else:
                    st.warning(f"{new_code} 已存在")
            else:
                st.error("代码必须是 6 位数字")

# 展示列表 & 删除按钮
self_list = load_self()
if self_list:
    st.write("**当前自选：**")
    for item in self_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"{item['code']} 📊", key=f"analyze_{item['code']}"):
                st.session_state["analyze_code"] = item["code"]
        with col2:
            if st.button("删", key=f"del_{item['code']}"):
                del_stock(item["code"])
                st.rerun()
else:
    st.info("暂无自选股，请在上方添加")

# ---------------- 单股分析 ----------------
st.markdown("---")
st.header("🔍 单股分析")
single_code = st.text_input("或直接输入代码快速分析", max_chars=6, key="single_code")
if st.button("开始分析", type="primary", key="single_analyze"):
    if single_code.isdigit() and len(single_code) == 6:
        st.session_state["analyze_code"] = single_code
    else:
        st.error("代码必须是 6 位数字")

# 统一分析入口
if "analyze_code" in st.session_state:
    code = st.session_state["analyze_code"]
    symbol = normalize_symbol(code)
    with st.spinner("正在获取数据并计算指标..."):
        try:
            df = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq").tail(150)
            if df.empty:
                st.error("未获取到数据，请检查代码是否正确")
                st.stop()
            df = compute_enhanced_indicators(df)
            div   = comprehensive_divergence_analysis(df)
            advice = generate_trading_advice(div, df)
            trend = analyze_trend(df)
            latest = df.iloc[-1]
        except Exception as e:
            st.exception(e)
            st.stop()

    # 展示
    col1, col2, col3 = st.columns(3)
    col1.metric("最新收盘价", f"{latest['close']:.2f}")
    col2.metric("当前趋势", trend)
    col3.metric("RSI (14)", f"{latest['rsi']:.1f}")

    st.subheader("💡 操作建议")
    st.info(advice)

    if div:
        level = div.get("level", "背离")
        if level == "强烈背离":
            st.success(f"🎯 检测到{level}（{len(div['signals'])}重确认，置信度 {div['confidence']:.0%}）")
        elif level == "小背离":
            st.warning(f"📊 检测到{level}（{len(div['signals'])}重确认，置信度 {div['confidence']:.0%}）")
        else:
            st.info(f"检测到背离信号（{len(div['signals'])}重确认，置信度 {div['confidence']:.0%}）")
        with st.expander("展开信号明细"):
            st.write("、".join(div["signals"]))
    else:
        st.warning("未检测到明显底背离形态")

    # 画图
    st.subheader("价格与均线")
    chart_df = df[['close']].copy()
    chart_df['MA5'] = df['ma5']
    chart_df['MA20'] = df['ma20']
    st.line_chart(chart_df)

    st.caption("风险提示：仅供技术研究，不构成投资建议，投资有风险，入市需谨慎。")