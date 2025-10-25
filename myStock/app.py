import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import akshare as ak

# =============================
# 系统配置
# =============================
st.set_page_config(page_title="股票量化系统", layout="wide")
DATA_FILE = "data/favorites.json"

# =============================
# 通用函数
# =============================
def load_favorites():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_favorites(favs):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)

# =============================
# 页面定义
# =============================

def dashboard_page():
    """📊 仪表板"""
    st.title("📊 股票量化系统 - 仪表板")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("上证指数")
        df_sh = ak.stock_zh_index_daily(symbol="sh000001").tail(100)
        df_sh["date"] = pd.to_datetime(df_sh["date"])
        st.line_chart(df_sh, x="date", y="close")

    with col2:
        st.subheader("深证成指")
        df_sz = ak.stock_zh_index_daily(symbol="sz399001").tail(100)
        df_sz["date"] = pd.to_datetime(df_sz["date"])
        st.line_chart(df_sz, x="date", y="close")

    st.markdown("---")
    st.header("📈 核心指标汇总（示例）")
    data = {
        "指标": ["总持仓收益率", "本周收益", "仓位占比", "策略信号数"],
        "数值": ["+8.2%", "+1.4%", "72%", "3个买入信号"],
    }
    st.table(pd.DataFrame(data))

def favorites_page():
    """📋 自选股"""
    st.title("📋 自选股管理")

    favorites = load_favorites()

    st.subheader("➕ 添加股票")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_code = st.text_input("股票代码（如 600519）", "")
    with col2:
        add_btn = st.button("添加")

    if add_btn and new_code:
        new_code = new_code.strip()
        if new_code not in favorites:
            favorites.append(new_code)
            save_favorites(favorites)
            st.success(f"已添加：{new_code}")
        else:
            st.warning("该股票已存在")

    st.subheader("📑 当前自选股")
    if favorites:
        df = pd.DataFrame({"股票代码": favorites})
        st.dataframe(df, use_container_width=True)

        del_code = st.selectbox("选择要删除的股票", [""] + favorites)
        if st.button("删除选中股票") and del_code:
            favorites = [x for x in favorites if x != del_code]
            save_favorites(favorites)
            st.success(f"已删除：{del_code}")
    else:
        st.info("暂无自选股，请先添加。")

# =============================
# 页面路由
# =============================

st.sidebar.title("📁 系统导航")
page = st.sidebar.radio(
    "选择功能模块",
    [
        "📊 仪表板",
        "📋 自选股",
        # 未来可扩展：
        # "💼 持仓列表",
        # "🔍 股票分析",
        # "⚙️ 系统设置"
    ],
)

if page == "📊 仪表板":
    dashboard_page()
elif page == "📋 自选股":
    favorites_page()
