from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

# ========== 初始化 Flask 应用 ==========
app = Flask(__name__)
# 跨域配置（通用，兼容所有前端平台）
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

# ========== 通用平台适配配置（核心，无硬编码） ==========
# 1. 端口适配：自动识别平台
# - Replit: 8080（环境变量 REPL_ID 存在）
# - Render: 读平台分配的 PORT 环境变量
# - 本地: 5000（兜底）
PORT = int(os.environ.get('PORT', 8080 if 'REPL_ID' in os.environ else 5000))

# 2. 数据库路径适配：按平台特性自动切换
# - Replit: .data/todos.db（持久化存储，重启不丢失）
# - Render: /tmp/todos.db（平台临时目录）
# - 本地: ./todos.db（项目根目录，方便调试）
if 'REPL_ID' in os.environ:  # Replit 环境标识
    os.makedirs('.data', exist_ok=True)  # 确保目录存在
    DB_FILE = '.data/todos.db'
elif 'RENDER' in os.environ:  # Render 环境标识
    DB_FILE = '/tmp/todos.db'
else:  # 本地开发环境
    DB_FILE = './todos.db'


# ========== 数据库初始化（通用逻辑） ==========
def init_database():
    """初始化 todos 表，通用逻辑适配所有平台"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # 创建 todos 表（不存在则创建）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()
        conn.close()
        print(f"✅ 数据库初始化成功 | 路径: {DB_FILE}")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")


# ========== 健康检查接口（新增平台标识，方便调试） ==========
@app.route('/api/health', methods=['GET'])
def health_check():
    # 识别当前部署平台
    platform = "Replit" if 'REPL_ID' in os.environ else "Render" if 'RENDER' in os.environ else "本地"
    return jsonify({
        "code": 200,
        "msg": f"部署成功（平台：{platform}）",
        "data": {
            "port": PORT,
            "db_path": DB_FILE,
            "platform": platform
        }
    })


# ========== 业务接口（完全保留你的核心逻辑） ==========
# 1. 获取所有待办
@app.route('/api/todos', methods=['GET'])
def get_todos():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # 让返回结果为字典格式
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM todos')
        todos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({
            "code": 200,
            "msg": "获取待办成功",
            "data": todos
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取待办失败: {str(e)}",
            "data": None
        }), 500


# 2. 新增待办
@app.route('/api/todos', methods=['POST'])
def add_todo():
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({
                "code": 400,
                "msg": "待办标题不能为空",
                "data": None
            }), 400

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO todos (title, completed) VALUES (?, ?)',
            (data['title'], False)
        )
        conn.commit()
        todo_id = cursor.lastrowid
        conn.close()

        return jsonify({
            "code": 201,
            "msg": "新增待办成功",
            "data": {
                "id": todo_id,
                "title": data['title'],
                "completed": False
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"新增待办失败: {str(e)}",
            "data": None
        }), 500


# 3. 切换待办状态
@app.route('/api/todos/<int:todo_id>/toggle', methods=['PUT'])
def toggle_todo(todo_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 检查待办是否存在
        cursor.execute('SELECT completed FROM todos WHERE id = ?', (todo_id,))
        todo = cursor.fetchone()
        if not todo:
            conn.close()
            return jsonify({
                "code": 404,
                "msg": "待办不存在",
                "data": None
            }), 404

        # 切换状态
        new_status = not todo[0]
        cursor.execute(
            'UPDATE todos SET completed = ? WHERE id = ?',
            (new_status, todo_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "code": 200,
            "msg": "状态更新成功",
            "data": {
                "id": todo_id,
                "completed": new_status
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"更新状态失败: {str(e)}",
            "data": None
        }), 500


# 4. 删除待办
@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 检查待办是否存在
        cursor.execute('SELECT id FROM todos WHERE id = ?', (todo_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                "code": 404,
                "msg": "待办不存在",
                "data": None
            }), 404

        cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
        conn.close()

        return jsonify({
            "code": 200,
            "msg": "删除待办成功",
            "data": None
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"删除待办失败: {str(e)}",
            "data": None
        }), 500


# 5. 编辑待办标题
@app.route('/api/todos/<int:todo_id>/edit', methods=['PUT'])
def edit_todo(todo_id):
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({
                "code": 400,
                "msg": "待办标题不能为空",
                "data": None
            }), 400

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 检查待办是否存在
        cursor.execute('SELECT id FROM todos WHERE id = ?', (todo_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({
                "code": 404,
                "msg": "待办不存在",
                "data": None
            }), 404

        cursor.execute(
            'UPDATE todos SET title = ? WHERE id = ?',
            (data['title'], todo_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "code": 200,
            "msg": "编辑待办成功",
            "data": {
                "id": todo_id,
                "title": data['title']
            }
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"编辑待办失败: {str(e)}",
            "data": None
        }), 500


# ========== 通用启动逻辑（无硬编码） ==========
if __name__ == '__main__':
    # 初始化数据库（确保表存在）
    init_database()
    # 启动服务：host 固定 0.0.0.0（外网可访问），port 读配置
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False  # 生产环境关闭 debug
    )