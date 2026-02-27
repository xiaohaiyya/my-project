# 待办核心接口
from flask import Blueprint, request, jsonify
import logging
from db import get_db_connection

# 创建蓝图
todos_bp = Blueprint('todos', __name__)
logger = logging.getLogger(__name__)


# ========== 待办统计接口 ==========
@todos_bp.route('/api/todos/stats', methods=['GET'])
def get_todo_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 总数
        cursor.execute('SELECT COUNT(*) FROM todos')
        total = cursor.fetchone()[0]
        # 已完成数
        cursor.execute('SELECT COUNT(*) FROM todos WHERE completed = 1')
        completed = cursor.fetchone()[0]
        # 未完成数
        uncompleted = total - completed

        conn.close()
        return jsonify({
            "code": 200,
            "msg": "获取统计数据成功",
            "data": {
                "total": total,
                "completed": completed,
                "uncompleted": uncompleted
            }
        })
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取统计数据失败: {str(e)}",
            "data": None
        }), 500


# ========== 获取待办（支持筛选+排序） ==========
@todos_bp.route('/api/todos', methods=['GET'])
def get_todos():
    try:
        # 获取筛选参数（all/completed/uncompleted）
        filter_type = request.args.get('filter', 'all')
        conn = get_db_connection()
        cursor = conn.cursor()

        # 按筛选条件查询，按创建时间倒序
        if filter_type == 'completed':
            cursor.execute('SELECT * FROM todos WHERE completed = 1 ORDER BY created_at DESC')
        elif filter_type == 'uncompleted':
            cursor.execute('SELECT * FROM todos WHERE completed = 0 ORDER BY created_at DESC')
        else:
            cursor.execute('SELECT * FROM todos ORDER BY created_at DESC')

        todos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        logger.info(f"获取待办成功 | 筛选类型: {filter_type} | 数量: {len(todos)}")
        return jsonify({
            "code": 200,
            "msg": "获取待办成功",
            "data": todos
        })
    except Exception as e:
        logger.error(f"获取待办失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取待办失败: {str(e)}",
            "data": None
        }), 500


# ========== 批量删除已完成待办 ==========
@todos_bp.route('/api/todos/clear-completed', methods=['DELETE'])
def clear_completed_todos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 删除已完成的待办
        cursor.execute('DELETE FROM todos WHERE completed = 1')
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"批量删除已完成待办 | 数量: {deleted_count}")
        return jsonify({
            "code": 200,
            "msg": f"成功删除 {deleted_count} 个已完成待办",
            "data": {"deleted_count": deleted_count}
        })
    except Exception as e:
        logger.error(f"批量删除失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"批量删除失败: {str(e)}",
            "data": None
        }), 500


# ========== 新增待办 ==========
@todos_bp.route('/api/todos', methods=['POST'])
def add_todo():
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({
                "code": 400,
                "msg": "待办标题不能为空",
                "data": None
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO todos (title, completed) VALUES (?, ?)',
            (data['title'], False)
        )
        conn.commit()
        todo_id = cursor.lastrowid
        # 获取新增的待办（含创建时间）
        cursor.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
        new_todo = dict(cursor.fetchone())
        conn.close()

        logger.info(f"新增待办成功 | ID: {todo_id}")
        return jsonify({
            "code": 201,
            "msg": "新增待办成功",
            "data": new_todo
        })
    except Exception as e:
        logger.error(f"新增待办失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"新增待办失败: {str(e)}",
            "data": None
        }), 500


# ========== 切换待办状态 ==========
@todos_bp.route('/api/todos/<int:todo_id>/toggle', methods=['PUT'])
def toggle_todo(todo_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT completed FROM todos WHERE id = ?', (todo_id,))
        todo = cursor.fetchone()
        if not todo:
            conn.close()
            return jsonify({
                "code": 404,
                "msg": "待办不存在",
                "data": None
            }), 404

        new_status = not todo[0]
        cursor.execute(
            'UPDATE todos SET completed = ? WHERE id = ?',
            (new_status, todo_id)
        )
        conn.commit()
        conn.close()

        logger.info(f"切换待办状态 | ID: {todo_id} | 新状态: {new_status}")
        return jsonify({
            "code": 200,
            "msg": "状态更新成功",
            "data": {
                "id": todo_id,
                "completed": new_status
            }
        })
    except Exception as e:
        logger.error(f"切换状态失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"更新状态失败: {str(e)}",
            "data": None
        }), 500


# ========== 删除单个待办 ==========
@todos_bp.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

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

        logger.info(f"删除待办成功 | ID: {todo_id}")
        return jsonify({
            "code": 200,
            "msg": "删除待办成功",
            "data": None
        })
    except Exception as e:
        logger.error(f"删除待办失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"删除待办失败: {str(e)}",
            "data": None
        }), 500


# ========== 编辑待办标题 ==========
@todos_bp.route('/api/todos/<int:todo_id>/edit', methods=['PUT'])
def edit_todo(todo_id):
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({
                "code": 400,
                "msg": "待办标题不能为空",
                "data": None
            }), 404

        conn = get_db_connection()
        cursor = conn.cursor()

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

        logger.info(f"编辑待办成功 | ID: {todo_id}")
        return jsonify({
            "code": 200,
            "msg": "编辑待办成功",
            "data": {
                "id": todo_id,
                "title": data['title']
            }
        })
    except Exception as e:
        logger.error(f"编辑待办失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"编辑待办失败: {str(e)}",
            "data": None
        }), 500