# 主启动文件：仅初始化+注册路由
from flask import Flask
from flask_cors import CORS
import logging
from config import PORT, CORS_ORIGINS, CORS_HEADERS, LOGGING_CONFIG
from db import init_database
from routes import health_bp, todos_bp

# ========== 初始化 Flask 应用 ==========
app = Flask(__name__)

# ========== 配置跨域 ==========
CORS(app, resources={r"/*": {"origins": CORS_ORIGINS}})
app.config['CORS_HEADERS'] = CORS_HEADERS

# ========== 配置日志 ==========
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format'],
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== 注册路由蓝图 ==========
app.register_blueprint(health_bp)
app.register_blueprint(todos_bp)

# ========== 启动服务 ==========
if __name__ == '__main__':
    # 初始化数据库
    init_database()
    # 启动应用
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False
    )