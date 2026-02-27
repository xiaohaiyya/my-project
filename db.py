# 数据库工具：封装连接、初始化逻辑
import sqlite3
import logging
from config import DB_FILE

# 初始化日志
logger = logging.getLogger(__name__)

def get_db_connection():
    """获取数据库连接（复用）"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise e

def init_database():
    """初始化数据库表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 创建待办表（含创建时间字段）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("数据库初始化成功（含创建时间字段）")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise e