# 在lims/__init__.py或与settings.py同级的__init__.py中添加
import pymysql
pymysql.install_as_MySQLdb()