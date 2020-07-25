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
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship('Todo', backref='todo_list_name', lazy=True)
    
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

'''
non - ajax version
# creating a route handler for creating a new todo record.
@app.route('/todos/create', methods=['POST'])
def create_todo():
    # getting the value of description and todoid from form. If the value is empty for description, then use default value which is a empty string.
    description = request.form.get('description', '')
    # creating a new todo object and inserting it in our database.
    todo = Todo(description=description)
    db.session.add(todo)
    db.session.commit()
    # after successful insertion of record, we can redirect to our home page. index is the route handler for our home page.
    return redirect(url_for('index'))

'''

# ajax version.
# creating a route handler for creating a new todo record.
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
    return redirect(url_for('index'))

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

# creating a route handler for displaying todos assosciated to a specific todo list id.
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
    return render_template('index.html', data=Todo.query.filter_by(list_id=list_id).order_by('id').all())

# creating a route handler for the homepage which will redirect to page which will show all todos for list id 1 , </lists/1>.
@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=1))