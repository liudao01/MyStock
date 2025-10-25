import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="自选股管理", layout="wide")

DATA_FILE = "data/favorites.json"

# === 初始化 ===
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

favorites = load_favorites()

# === 页面标题 ===
st.title("📋 自选股管理")

# === 添加新股票 ===
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

# === 显示自选股列表 ===
st.subheader("📑 当前自选股")

if favorites:
    df = pd.DataFrame({"股票代码": favorites})
    st.dataframe(df, use_container_width=True)

    # 删除操作
    del_code = st.selectbox("选择要删除的股票", [""] + favorites)
    if st.button("删除选中股票") and del_code:
        favorites = [x for x in favorites if x != del_code]
        save_favorites(favorites)
        st.success(f"已删除：{del_code}")
else:
    st.info("暂无自选股，请先添加。")

