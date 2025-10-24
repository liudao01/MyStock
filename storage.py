"""
自选股 JSON 存取
"""
import json
import os
import akshare as ak

SELF_SEL_FILE = "self_selection.json"


# ---------- 工具：拿股票简称 ----------
def _query_stock_name(symbol: str) -> str:
    """
    根据 sh/sz/bj/纯代码 返回股票简称，失败返回原串
    """
    code = symbol.strip().lower()
    for pre in ("sh", "sz", "bj"):
        if code.startswith(pre):
            code = code[2:]
            break
    try:
        all_list = ak.stock_info_a_code_name()          # DataFrame
        hit = all_list.loc[all_list["code"] == code, "name"]
        return hit.values[0] if not hit.empty else symbol
    except Exception:
        from analysis import get_stock_name              # 兜底
        return get_stock_name(symbol)


# ---------- 增删查存 ----------
def load_self():
    if not os.path.exists(SELF_SEL_FILE):
        return []
    with open(SELF_SEL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_self(data):
    with open(SELF_SEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_stock(code: str, name: str = "") -> bool:
    """新增自选股；name 留空则自动查简称"""
    from analysis import normalize_symbol
    code = normalize_symbol(code)
    lst = load_self()
    if any(item["code"] == code for item in lst):
        return False                                    # 已存在
    name = name or _query_stock_name(code)
    lst.append({"code": code, "name": name})
    save_self(lst)
    return True


def del_stock(code):
    from analysis import normalize_symbol
    code = normalize_symbol(code)
    lst = [item for item in load_self() if item["code"] != code]
    save_self(lst)