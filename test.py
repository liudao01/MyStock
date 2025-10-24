import akshare as ak

def get_stock_name(symbol: str) -> str:
    """
    根据股票代码获取股票名称（支持 sz/sh/bj）
    例如: sz000001, sh600519, bj430047
    """
    try:
        # 清洗代码前缀
        if symbol.startswith("sz"):
            code = symbol[2:]
            market = "sz"
        elif symbol.startswith("sh"):
            code = symbol[2:]
            market = "sh"
        elif symbol.startswith("bj"):
            code = symbol[2:]
            market = "bj"
        else:
            code = symbol
            market = "sz"

        stock_list = ak.stock_info_a_code_name()  # 获取沪深所有股票列表
        name = stock_list.loc[stock_list["code"] == code, "name"]
        if not name.empty:
            return name.values[0]
        else:
            return f"未找到股票代码 {symbol} 对应名称"
    except Exception as e:
        return f"查询出错: {e}"

if __name__ == "__main__":
    while True:
        code = input("请输入股票代码（例如 sz000617）：").strip()
        if code.lower() in ["exit", "q"]:
            break
        print("股票名称：", get_stock_name(code))
