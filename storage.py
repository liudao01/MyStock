"""
自选股 JSON 存取
"""
import json
import os

SELF_SEL_FILE = "self_selection.json"

# ---------- 基础 CRUD ----------
def load_self():
    if not os.path.exists(SELF_SEL_FILE):
        return []
    with open(SELF_SEL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_self(data):
    with open(SELF_SEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_stock(code: str, name: str = "") -> bool:
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

    