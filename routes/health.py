# 健康检查接口
from flask import Blueprint, jsonify
from config import PORT, DB_FILE
import os

# 创建蓝图（模块化路由）
health_bp = Blueprint('health', __name__)


@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    # 判断运行平台
    if 'REPL_ID' in os.environ:
        platform = "Replit"
    elif 'RENDER' in os.environ:
        platform = "Render"
    else:
        platform = "本地"

    return jsonify({
        "code": 200,
        "msg": f"部署成功（平台：{platform}）",
        "data": {
            "port": PORT,
            "db_path": DB_FILE,
            "platform": platform
        }
    })