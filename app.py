# 导入核心依赖
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
import traceback

# 初始化 Flask 应用
app = Flask(__name__)

# 配置跨域（开发/演示阶段允许所有域名，上线后可替换为你的 Vercel 前端域名）
# 示例：CORS(app, resources={r"/*": {"origins": "https://your-react-app.vercel.app"}})
CORS(app, resources={r"/*": {"origins": "*"}})

# ===================== 核心配置 =====================
# SQLite 数据库路径（适配 Render 服务器的文件系统）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'data.db')

# ===================== 数据库工具函数 =====================
def get_db_connection():
    """获取数据库连接（封装成函数，方便复用）"""
    try:
        conn = sqlite3.connect(DB_FILE)
        # 设置行工厂，让查询结果以字典形式返回（更易用）
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        app.logger.error(f"数据库连接失败: {str(e)}")
        raise e

# 初始化数据库（确保表存在，首次部署自动创建）
def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 示例：创建一个测试表（你可以替换成自己的业务表）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 启动时初始化数据库
init_database()

# ===================== 接口定义 =====================
@app.route('/')
def index():
    """根路径测试"""
    return jsonify({
        "code": 200,
        "msg": "Flask 后端服务已启动（Render 部署成功）",
        "data": {
            "service": "flask-backend",
            "database": "SQLite",
            "status": "running"
        }
    })

@app.route('/api/test', methods=['GET'])
def test_connection():
    """测试接口：验证数据库连接和服务可用性"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 测试查询
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()

        return jsonify({
            "code": 200,
            "msg": "后端部署成功！SQLite 数据库连接正常",
            "data": {
                "db_test": result[0],  # 应返回 1
                "db_path": DB_FILE
            }
        })
    except Exception as e:
        # 打印错误日志（Render 可查看）
        app.logger.error(f"测试接口异常: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "code": 500,
            "msg": f"接口调用失败: {str(e)}",
            "data": None
        }), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """示例业务接口：获取所有用户"""
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT * FROM users').fetchall()
        conn.close()

        # 转换为列表字典（方便前端解析）
        user_list = [dict(user) for user in users]
        return jsonify({
            "code": 200,
            "msg": "获取用户列表成功",
            "data": user_list
        })
    except Exception as e:
        app.logger.error(f"获取用户异常: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取用户失败: {str(e)}",
            "data": None
        }), 500

@app.route('/api/users', methods=['POST'])
def add_user():
    """示例业务接口：添加用户"""
    try:
        # 获取前端传参
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({
                "code": 400,
                "msg": "参数错误：name 不能为空",
                "data": None
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email) VALUES (?, ?)',
            (data.get('name'), data.get('email', ''))
        )
        conn.commit()
        conn.close()

        return jsonify({
            "code": 201,
            "msg": "用户添加成功",
            "data": {
                "name": data.get('name'),
                "email": data.get('email', '')
            }
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({
            "code": 409,
            "msg": "邮箱已存在",
            "data": None
        }), 409
    except Exception as e:
        app.logger.error(f"添加用户异常: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"添加用户失败: {str(e)}",
            "data": None
        }), 500

# ===================== 启动配置 =====================
if __name__ == '__main__':
    # 从环境变量读取端口（Render 自动分配），默认 5000
    port = int(os.environ.get('PORT', 5000))
    # 生产环境关闭 debug，绑定 0.0.0.0 允许外部访问
    app.run(host='0.0.0.0', port=port, debug=False)