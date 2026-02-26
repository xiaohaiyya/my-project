from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # 导入跨域插件
import datetime
import os

app = Flask(__name__)
# 允许跨域（关键：让Vue前端能访问）
CORS(app, resources=r"/*")

# 数据库配置（和之前一致）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'timeout': 5, 'check_same_thread': False},
    'pool_size': 1, 'max_overflow': 0
}
db = SQLAlchemy(app)


# 数据模型（和之前一致）
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)


# 初始化数据库
with app.app_context():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    db.create_all()


# ========== 核心：API接口（替代原有模板渲染） ==========
# 1. 获取所有待办
@app.route('/api/todos', methods=['GET'])
def get_todos():
    try:
        todos = Todo.query.order_by(Todo.created_at.desc()).all()
        # 转成JSON格式（关键：只返回数据，不渲染页面）
        todo_list = [{
            'id': todo.id,
            'title': todo.title,
            'completed': todo.completed,
            'created_at': todo.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for todo in todos]
        return jsonify({'code': 200, 'data': todo_list})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'查询失败：{str(e)}'})


# 2. 添加待办
@app.route('/api/todos', methods=['POST'])
def add_todo():
    try:
        data = request.get_json()  # 接收Vue传的JSON数据
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'code': 400, 'msg': '标题不能为空'})

        new_todo = Todo(title=title)
        db.session.add(new_todo)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '添加成功', 'data': {'id': new_todo.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'添加失败：{str(e)}'})


# 3. 切换待办状态
@app.route('/api/todos/<int:todo_id>/toggle', methods=['PUT'])
def toggle_todo(todo_id):
    try:
        todo = Todo.query.get(todo_id)
        if not todo:
            return jsonify({'code': 404, 'msg': '待办不存在'})

        todo.completed = not todo.completed
        db.session.commit()
        return jsonify({'code': 200, 'msg': '状态更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'更新失败：{str(e)}'})


# 4. 删除待办
@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        todo = Todo.query.get(todo_id)
        if not todo:
            return jsonify({'code': 404, 'msg': '待办不存在'})

        db.session.delete(todo)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'删除失败：{str(e)}'})

# 5. 编辑待办
@app.route('/api/todos/<int:todo_id>/edit', methods=['PUT'])
def edit_todo(todo_id):
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'code': 400, 'msg': '标题不能为空'})

        todo = Todo.query.get(todo_id)
        if not todo:
            return jsonify({'code': 404, 'msg': '待办不存在'})

        todo.title = title
        db.session.commit()
        return jsonify({'code': 200, 'msg': '编辑成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'编辑失败：{str(e)}'})


# 运行后端
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)  # host=0.0.0.0 允许前端访问