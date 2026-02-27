from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime

# 初始化 Flask 应用
app = Flask(__name__)

# ========== 1. 跨域配置（适配 Render + 前端 Vercel） ==========
CORS(app, resources={r"/*": {"origins": "*"}})

# ========== 2. SQLite 路径适配（Render 核心！仅 /tmp 目录可写） ==========
if 'RENDER' in os.environ:
    DB_FILE = '/tmp/todos.db'
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_FILE = os.path.join(BASE_DIR, 'todos.db')


# ========== 3. 数据库工具函数（不变） ==========
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("数据库初始化成功！")
    except Exception as e:
        print(f"数据库初始化失败：{str(e)}")


init_database()


# ========== 新增：Render 部署测试接口（核心！） ==========
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口，验证 Render 部署是否成功"""
    return jsonify({
        "code": 200,
        "msg": "Render 部署成功！后端服务正常运行",
        "data": {
            "env": "Render 生产环境" if 'RENDER' in os.environ else "本地开发环境",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"
        }
    })


# ========== 4. 原有业务接口（完全不变） ==========
# 获取所有待办
@app.route('/api/todos', methods=['GET'])
def get_todos():
    try:
        conn = get_db_connection()
        todos = conn.execute('SELECT * FROM todos ORDER BY created_at DESC').fetchall()
        conn.close()
        todo_list = [dict(todo) for todo in todos]
        return jsonify({"code": 200, "msg": "获取成功", "data": todo_list})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取失败：{str(e)}", "data": None}), 500


# 新增待办
@app.route('/api/todos', methods=['POST'])
def add_todo():
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({"code": 400, "msg": "标题不能为空", "data": None}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO todos (title) VALUES (?)', (data['title'],))
        conn.commit()
        conn.close()
        return jsonify({"code": 200, "msg": "添加成功", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"添加失败：{str(e)}", "data": None}), 500


# 切换待办状态
@app.route('/api/todos/<int:todo_id>/toggle', methods=['PUT'])
def toggle_todo(todo_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE todos SET completed = NOT completed WHERE id = ?', (todo_id,))
        conn.commit()
        conn.close()
        return jsonify({"code": 200, "msg": "状态更新成功", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"状态更新失败：{str(e)}", "data": None}), 500


# 删除待办
@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
        conn.close()
        return jsonify({"code": 200, "msg": "删除成功", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}", "data": None}), 500


# 编辑待办
@app.route('/api/todos/<int:todo_id>/edit', methods=['PUT'])
def edit_todo(todo_id):
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({"code": 400, "msg": "标题不能为空", "data": None}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE todos SET title = ? WHERE id = ?', (data['title'], todo_id))
        conn.commit()
        conn.close()
        return jsonify({"code": 200, "msg": "编辑成功", "data": None})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"编辑失败：{str(e)}", "data": None}), 500


# ========== 5. 启动配置（适配 Render 端口规则） ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)