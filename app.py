from flask import Flask, jsonify, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
# Modify this string with the appropriate database connection settings you have set up in your machine.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 30

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class TodoList(db.Model):
    # Table name
    __tablename__ = 'todolist'
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship('Todo', backref='todolist',
                            lazy=True, cascade='all, delete', passive_deletes=True)

    # Object Representation
    def __repr__(self):
        return f"\n<TodoList id:{self.id} name:{self.name}>"


class Todo(db.Model):
    # Table name
    __tablename__ = 'todo'
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    todolist_id = db.Column(db.Integer, db.ForeignKey(
        "todolist.id", ondelete="CASCADE"), nullable=False)

    # Object Representation
    def __repr__(self):
        return f"\n<Todo id:{self.id}, description:{self.description} completed:{self.completed}>"

# Commented due to our use of migrations
# db.create_all()

# ------------------ Create Todo ------------------
@app.route('/todos/<int:todolist_id>', methods=['POST'])
def create_todo(todolist_id):
    data = request.get_json()
    description = data.get('description')

    if not description:
        abort(400, description="Missing description")

    todo = Todo(description=description, todolist_id=todolist_id)
    try:
        db.session.add(todo)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(400, description=str(e))

    return jsonify({
        'id': todo.id,
        'description': todo.description
    })


# ------------------ Create Todo List ------------------
@app.route('/todos', methods=['POST'])
def create_list():
    data = request.get_json()
    name = data.get('name')

    if not name:
        abort(400, description="Missing list name")

    todo_list = TodoList(name=name)
    try:
        db.session.add(todo_list)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(400, description=str(e))

    return jsonify({
        'id': todo_list.id,
        'name': todo_list.name
    })


# ------------------ Update Todo ------------------
@app.route('/todos/<int:list_id>/<int:todo_id>', methods=['PATCH'])
def update_todo(list_id, todo_id):
    data = request.get_json()
    completed = data.get('completed')
    if completed is None:
        abort(400, description="Missing completed status")

    todo = Todo.query.get_or_404(todo_id)
    todo.completed = completed
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(400, description=str(e))

    return jsonify({'completed': todo.completed})


# ------------------ Mark all todos completed ------------------
@app.route('/todos/<int:list_id>', methods=['PUT'])
def update_all(list_id):
    todos = Todo.query.filter_by(todolist_id=list_id).all()
    for todo in todos:
        todo.completed = True
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(400, description=str(e))

    return jsonify({'successful': True})


# ------------------ Delete Todo ------------------
@app.route('/todos/<int:list_id>/<int:todo_id>', methods=["DELETE"])
def delete_todo(list_id, todo_id):
    todo = Todo.query.get_or_404(todo_id)
    try:
        db.session.delete(todo)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(400, description=str(e))

    return jsonify({'successful': True})


# ------------------ Delete Todo List ------------------
@app.route('/todos/<int:list_id>', methods=["DELETE"])
def delete_list(list_id):
    todo_list = TodoList.query.get_or_404(list_id)
    try:
        db.session.delete(todo_list)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(400, description=str(e))

    return jsonify({'successful': True})


# ------------------ Get Todos for a List ------------------
@app.route('/todos/<int:list_id>')
def get_todo_list(list_id):
    todo_list = TodoList.query.get_or_404(list_id)
    todos = Todo.query.filter_by(todolist_id=list_id).order_by(Todo.id).all()
    all_lists = TodoList.query.order_by(TodoList.id).all()

    return render_template('index.html', data=todos, list_id=list_id, list=all_lists, name=todo_list.name)


# ------------------ Default Route ------------------
@app.route('/')
def index():
    first_list = TodoList.query.first()
    if first_list:
        return redirect(url_for('get_todo_list', list_id=first_list.id))
    else:
        # No lists exist yet
        return redirect(url_for('get_todo_list', list_id=0))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5001)
