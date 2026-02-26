# 导入必要的库
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import datetime

# 初始化 Flask 应用
app = Flask(__name__)

# 配置 SQLite 数据库（todo.db 会自动生成在项目根目录）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭不必要的警告

# 初始化数据库
db = SQLAlchemy(app)

# 定义待办事项模型（对应数据库表）
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 唯一ID（主键）
    title = db.Column(db.String(100), nullable=False)  # 待办标题（不能为空）
    completed = db.Column(db.Boolean, default=False)  # 是否完成（默认未完成）
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)  # 创建时间

# 创建数据库表（首次运行时执行）
with app.app_context():
    db.create_all()

# 首页路由：展示所有待办事项
@app.route('/')
def index():
    # 查询所有待办事项，按创建时间倒序排列
    todos = Todo.query.order_by(Todo.created_at.desc()).all()
    # 渲染模板，把待办数据传给前端
    return render_template('index.html', todos=todos)

# 添加待办事项路由（接收POST请求）
@app.route('/add', methods=['POST'])
def add_todo():
    # 获取前端表单提交的标题
    title = request.form.get('title')
    # 简单验证：标题不为空才添加
    if title and title.strip():
        new_todo = Todo(title=title.strip())  # 创建新待办对象
        db.session.add(new_todo)  # 添加到数据库会话
        db.session.commit()  # 提交会话（保存到数据库）
    # 重定向回首页
    return redirect(url_for('index'))

# 标记待办完成/未完成路由
@app.route('/toggle/<int:todo_id>')
def toggle_todo(todo_id):
    # 根据ID查询待办，不存在则返回404
    todo = Todo.query.get_or_404(todo_id)
    # 切换完成状态
    todo.completed = not todo.completed
    db.session.commit()
    return redirect(url_for('index'))

# 删除待办事项路由
@app.route('/delete/<int:todo_id>')
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)  # 删除待办
    db.session.commit()
    return redirect(url_for('index'))

# 运行应用（仅在直接运行app.py时生效）
if __name__ == '__main__':
    app.run(debug=False)  # debug=True：代码修改后自动重启（开发环境用）