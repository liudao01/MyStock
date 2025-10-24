"""
Streamlit 前端 - 增加背离可视化图表
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
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
            btn_txt = f"{item['code']} {item.get('name', '')} 📊".strip()
            if st.button(btn_txt, key=f"analyze_{item['code']}"):
                st.session_state["analyze_code"] = item["code"]
        with col2:
            if st.button("删", key=f"del_{item['code']}"):
                del_stock(item["code"])
                st.rerun()
else:
    st.info("暂无自选股，请在上方添加")

# ---------------- 单股分析 ----------------
st.markdown("---")

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
    # ===== 这里放标题，保证 symbol 已就绪 =====
    st.header(f"🔍 单股分析 —— {get_stock_name(symbol)}")
    with st.spinner("正在获取数据并计算指标..."):
        try:
            df = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq").tail(150)
            if df.empty:
                st.error("未获取到数据，请检查代码是否正确")
                st.stop()
            df = compute_enhanced_indicators(df)
            # 修改这里：接收两个返回值
            div, error_msg = comprehensive_divergence_analysis(df)
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

    if error_msg:
        st.error("背离分析失败")
        with st.expander("查看计算过程"):
            st.text(error_msg)
    elif div:
        level = div.get("level", "背离")
        if level == "强烈背离":
            st.success(f"🎯 检测到{level}（{len(div['signals'])}重确认，置信度 {div['confidence']:.0%}）")
        elif level == "小背离":
            st.warning(f"📊 检测到{level}（{len(div['signals'])}重确认，置信度 {div['confidence']:.0%}）")
        else:
            st.info(f"检测到背离信号（{len(div['signals'])}重确认，置信度 {div['confidence']:.0%}）")
        
        # 显示检测到的信号
        st.subheader("✅ 检测到的背离信号")
        for signal in div['signals']:
            st.write(f"- {signal}")
        
        # ========== 新增：背离可视化图表 ==========
        st.subheader("📊 背离可视化")
        
        # 创建子图：价格和MACD
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=('价格走势与背离标记', 'MACD指标'),
            row_width=[0.7, 0.3]
        )
        
        # 重置索引以便按位置访问
        df_reset = df.reset_index()
        dates = pd.to_datetime(df_reset["date"]) if "date" in df_reset.columns else pd.to_datetime(df_reset.index)
        
        # 第一子图：价格和均线
        fig.add_trace(
            go.Scatter(x=dates, y=df_reset["close"], name="收盘价", line=dict(color='black', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=dates, y=df_reset["ma5"], name="MA5", line=dict(color='blue', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=dates, y=df_reset["ma20"], name="MA20", line=dict(color='orange', width=1)),
            row=1, col=1
        )
        
        # 标记背离的低点
        date1_idx = dates[dates == div['date1']].index[0]
        date2_idx = dates[dates == div['date2']].index[0]
        
        # 添加低点标记
        fig.add_trace(
            go.Scatter(
                x=[div['date1'], div['date2']],
                y=[div['price1'], div['price2']],
                mode='markers+text',
                marker=dict(size=12, color='red', symbol='circle'),
                text=[f"低点A", f"低点B"],
                textposition="top center",
                name="背离低点",
                hovertemplate="<b>%{text}</b><br>日期: %{x}<br>价格: %{y:.2f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 添加连接线
        fig.add_trace(
            go.Scatter(
                x=[div['date1'], div['date2']],
                y=[div['price1'], div['price2']],
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                showlegend=False,
                hovertemplate=None
            ),
            row=1, col=1
        )
        
        # 第二子图：MACD
        fig.add_trace(
            go.Scatter(x=dates, y=df_reset["macd"], name="MACD", line=dict(color='purple', width=1)),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=dates, y=df_reset["macd_dif"], name="DIF", line=dict(color='blue', width=1)),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=dates, y=df_reset["macd_signal"], name="DEA", line=dict(color='red', width=1)),
            row=2, col=1
        )
        
        # 标记MACD低点
        fig.add_trace(
            go.Scatter(
                x=[div['date1'], div['date2']],
                y=[div['macd1'], div['macd2']],
                mode='markers+text',
                marker=dict(size=10, color='green', symbol='diamond'),
                text=[f"MACD: {div['macd1']:.4f}", f"MACD: {div['macd2']:.4f}"],
                textposition="top center",
                name="MACD低点",
                hovertemplate="<b>%{text}</b><br>日期: %{x}<br>MACD: %{y:.4f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        # 添加MACD连接线
        fig.add_trace(
            go.Scatter(
                x=[div['date1'], div['date2']],
                y=[div['macd1'], div['macd2']],
                mode='lines',
                line=dict(color='green', width=2, dash='dash'),
                showlegend=False,
                hovertemplate=None
            ),
            row=2, col=1
        )
        
        # 更新图表布局
        fig.update_layout(
            height=600,
            title_text=f"底背离可视化 - {get_stock_name(symbol)}",
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # 更新y轴标题
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="MACD", row=2, col=1)
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True)
        
        # 图表说明
        st.markdown("""
        **图表说明:**
        - **上图**: 价格走势，红色虚线连接两个背离低点
        - **下图**: MACD指标，绿色虚线连接MACD低点
        - **背离特征**: 价格创新低(低点B < 低点A)，但MACD指标抬高(低点B > 低点A)
        """)
        
        # 显示详细计算过程
        with st.expander("🔍 查看详细计算过程"):
            st.text(div.get('calculation_steps', '无计算过程记录'))
    else:
        st.warning("未检测到明显底背离形态")

    # 原有的简单图表
    st.subheader("价格与均线")
    chart_df = df[['close']].copy()
    chart_df['MA5'] = df['ma5']
    chart_df['MA20'] = df['ma20']
    st.line_chart(chart_df)

    st.caption("风险提示：仅供技术研究，不构成投资建议，投资有风险，入市需谨慎。")