# 可选：在未安装 mysqlclient 时，使用 PyMySQL 作为 MySQLdb 兼容层。
try:
    import pymysql  # type: ignore
    pymysql.install_as_MySQLdb()
except Exception:
    # 若未安装 PyMySQL，则使用系统已安装的 mysqlclient (MySQLdb)。
    pass