# 配置文件：集中管理所有配置项
import os

# 端口配置
PORT = int(os.environ.get('PORT', 8080 if 'REPL_ID' in os.environ else 5000))

# 数据库路径配置
if 'REPL_ID' in os.environ:
    os.makedirs('.data', exist_ok=True)
    DB_FILE = '.data/todos.db'
elif 'RENDER' in os.environ:
    DB_FILE = '/tmp/todos.db'
else:
    DB_FILE = './todos.db'

# 跨域配置
CORS_ORIGINS = "*"  # 生产环境可改为具体域名
CORS_HEADERS = "Content-Type"

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'handlers': ['stream']
}