"""
自选股 JSON 存取
"""
import json
import os

SELF_SEL_FILE = "self_selection.json"
# -------------- 新增：真正靠得住的“查全称” --------------
import akshare as ak

def _query_stock_name(symbol: str) -> str:
    """
    优先用全市场列表精确匹配，失败再回退到 em 接口
    symbol: sh600519 / sz000001 / bj430047 / 600519
    """
    # 1. 统一成纯代码
    code = symbol.strip().lower()
    for prefix in ("sh", "sz", "bj"):
        if code.startswith(prefix):
            code = code[2:]
            break

    try:
        # 2. 全市场列表一次拉取，本地匹配
        all_list = ak.stock_info_a_code_name()      # DataFrame: [code, name]
        hit = all_list.loc[all_list["code"] == code, "name"]
        if not hit.empty:
            return hit.values[0]
    except Exception:
        pass

    # 3. 兜底：用 em 接口
    from analysis import get_stock_name
    return get_stock_name(symbol)


# -------------- 改造后的 add_stock --------------
def add_stock(code: str, name: str = "") -> bool:
    from analysis import normalize_symbol
    code = normalize_symbol(code)          # sh/sz 前缀化
    lst = load_self()
    if any(item["code"] == code for item in lst):
        return False                       # 已存在

    name = name or _query_stock_name(code) # 自动查全称
    lst.append({"code": code, "name": name})
    save_self(lst)
    return True

# ---------- 基础 CRUD ----------
def load_self():
    if not os.path.exists(SELF_SEL_FILE):
        return []
    with open(SELF_SEL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_self(data):
    with open(SELF_SEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


    """新增自选股；查不到名称时 name 留空"""
    from analysis import normalize_symbol, get_stock_name
    code = normalize_symbol(code)
    lst = load_self()
    if any(item["code"] == code for item in lst):
        return False  # 已存在

    if not name:  # 自动查名称
        name = get_stock_name(code)
        if name == code:  # 查询失败
            name = ""  # 留空

    lst.append({"code": code, "name": name})
    save_self(lst)
    return True

def del_stock(code):
    from analysis import normalize_symbol
    code = normalize_symbol(code)
    lst = [item for item in load_self() if item["code"] != code]
    save_self(lst)

    