from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
import sys

# Flask is a class that allows us to create an application. It creates an application named after the name of the file.
app = Flask(__name__)
# connecting the database from our flask app by setting a configuration variable present in a dictionary called app.config.
# postgresql://username:password@localhost:5432/dbname.
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///todoapp'

# linking our flask application with the database and returning the database instance.
# expire_on_commit default to True. When True, all instances will be fully expired after each commit(), so that all attributes/object accesses subsequent
# to a completed transcation will load from the most recent database state.
'''
db = SQLAlchemy(app, session_options={
    "expire_on_commit": False
})
'''

db = SQLAlchemy(app)

# linking the migrate object to our Flask app as well as our SQLAlchemy database. What migrate will do is start it up so that we can start
# using the Flask database migrate commands to began initializing migrations and upgrading and downgrading and generating migrations as well.
migrate = Migrate(app, db)

# creating the parent model TodoList and adding a one to many relationship betwwen TodoList and Todos Model.
class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, unique=True)
    todos = db.relationship('Todo', backref='todo_list_name', lazy=True, cascade='all, delete')
    
    def __repr__(self):
        return f'<TodoList {self.id} {self.name}>'

# creating our child model and adding a foreign key constraint list_id which will map to primary key id in TodoList model.
class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)
    
    def __repr__(self):
        return f'<Todo {self.id} {self.description} {self.list_id}>'

# commenting the create_all() function because we ll be using migrations for syncing our models or updating the database schema or downgrading it 
# in the future.
# db.create_all()

# creating a route handler for displaying a form to create a new todo list.
@app.route('/create/list/form')
def create_todo_list_form():
    return render_template('createtodolist.html')

# creating a route handler for displaying a form for renaming the active todo list.
@app.route('/todos/list/<active_todo_list_id>/form')
def display_form_rename_active_todo_list(active_todo_list_id):
    return render_template('renameactivetodolist.html', active_todo_list_id=active_todo_list_id)

# creating a route handler for displaying a form for creating a todo.
@app.route('/list/<active_todo_list_id>/todos/create/form')
def display_form_create_todo(active_todo_list_id):
    return render_template('createtodo.html', active_todo_list_id=active_todo_list_id)

# creating a route handler for creating a todo and assosciating that todo with the right todo list.
@app.route('/list/<active_todo_list_id>/todos/create', methods=['POST'])
def create_todo(active_todo_list_id):
    try:
        description = request.form.get('description', '')
        active_todo_list = TodoList.query.get(active_todo_list_id)
        new_todo = Todo(description=description)
        new_todo.todo_list_name = active_todo_list
        db.session.add(new_todo)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('get_list_todos', list_id=active_todo_list_id))

# creating a route handler for renaming the active todo list.
@app.route('/todos/active/list/<active_todo_list_id>/rename', methods=['POST'])
def rename_active_todo_list(active_todo_list_id):
    try:
        active_todo_list = TodoList.query.get(active_todo_list_id)
        name = request.form.get('new-todo-list-name')
        active_todo_list.name = name
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('get_list_todos', list_id=active_todo_list_id))

# creating a route handler for search functionality.
@app.route('/todo/list/<active_todo_list_id>/search/todos', methods=['POST'])
def search_todos(active_todo_list_id):
    match_todos = []
    description = request.form.get('search', '')
    todos = Todo.query.filter_by(list_id=active_todo_list_id).all()
    for todo in todos:
        if description.lower() in todo.description.lower():
            match_todos.append(todo)
    return render_template('index.html',
                           todo_lists = TodoList.query.order_by('id').all(),
                           active_todo_list = TodoList.query.get(active_todo_list_id),
                           todos=match_todos)
    

# creating a route handler for marking all todos completed.
@app.route('/list/<active_list_id>/complete/all/todos')
def complete_all_todos(active_list_id):
    try:
        todos = Todo.query.filter_by(list_id=active_list_id).all()
        for todo in todos:
            if todo.completed == False:
                todo.completed = True
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('get_list_todos', list_id=active_list_id))

# creating a route handler for adding a new todo list to the database and then displaying it with its respective todos in home page.
@app.route('/todos/create/list', methods=['POST'])
def create_new_todo_list():
    try:
        name = request.form.get('todo-list-name')
        todo_list = TodoList(name=name)
        db.session.add(todo_list)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('index'))

# ajax version.
# creating a route handler for creating a new todo record.
'''
@app.route('/todos/create', methods=['POST'])
def create_todo():
    error = False
    body = {}
    try:
        description = request.get_json()['description']
        todo = Todo(description=description, completed=False)
        db.session.add(todo)
        db.session.commit()
        body['description'] = todo.description
    except:
        error = True
        db.session.rollback()
        # print execution information which will be a useful debugging statement.
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        # return a json object as a response.
        return jsonify(body)
    else:
        abort(400)
'''
        
# ajax version.
# create a route handler for updating the completed state of a todo item.
@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
    try:
        completed = request.get_json()['completed']
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})

# ajax version
# create a route handler for deleting the todo object.
@app.route('/todos/<todo_id>/delete', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        todo = Todo.query.get(todo_id)
        db.session.delete(todo)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})

# ajax version
# create a route handler for deleting the entire todo list.
@app.route('/list/todos/<todo_list_id>/delete', methods=['DELETE'])
def delete_todo_list(todo_list_id):
    try:
        todo_list = TodoList.query.get(todo_list_id)
        db.session.delete(todo_list)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify({'success': True})

# creating a route handler for displaying todos assosciated to a specific todo list id. Also passing active todo list name and all todo lists 
# which will be displayed on the left hand side.
@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    '''
    This function will return a template file called index.html. Flask offers a method called
    render_template(). By default, flask looks for templates i.e html files in a folder called
    templates located in your project directory. We can actually pass variables from server to templates.
    Flask processes html templates using a templating engine called jinja or jinja2 which allows you to embedd non-html
    content in html files. It processes the entire file to replace the template strings that were in your html files with
    strings and then render an html file to the user. This variable data is a list of objects.
    '''
    todo_lists = TodoList.query.order_by('id').all()
    if len(todo_lists) == 0:
        return redirect(url_for('empty_todo_lists', list_id=-1))
    todo_list = TodoList.query.get(list_id)
    if todo_list == None:
        return redirect(url_for('empty_todo_lists', list_id=todo_lists[0].id))    
    return render_template('index.html',
                           todo_lists = todo_lists,
                           active_todo_list = todo_list,
                           todos=Todo.query.filter_by(list_id=list_id).order_by('id').all())

# creating a route handler to handle empty todo lists and deletion of active todo list.
@app.route('/todo/lists/<list_id>')
def empty_todo_lists(list_id):
    if int(list_id) == -1:
        return render_template('index.html', 
                           todo_lists = None,
                           active_todo_list = None,
                           todos=None)
    return redirect(url_for('get_list_todos', list_id=list_id))

# creating a route handler for the homepage which will redirect to page which will show all todos for smallest list id.
@app.route('/')
def index():
    todo_list_data = TodoList.query.order_by('id').all()
    if len(todo_list_data) == 0:
        return redirect(url_for('empty_todo_lists', list_id=-1))
    return redirect(url_for('get_list_todos', list_id=todo_list_data[0].id))