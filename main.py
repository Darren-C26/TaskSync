from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///boards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_COOKIE_NAME'] = 'task_sync_cookie'
app.config['SESSION_COOKIE_SECURE'] = True  # Set to False if not using HTTPS in development
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255), default='default_profile.png')

# Define the KanbanBoard, KanbanColumn, and Task models
class KanbanBoard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    columns = db.relationship('KanbanColumn', backref='board', lazy=True)

class KanbanColumn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    board_id = db.Column(db.Integer, db.ForeignKey('kanban_board.id'), nullable=False)
    tasks = db.relationship('Task', backref='column', lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    column_id = db.Column(db.Integer, db.ForeignKey('kanban_column.id'), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# API endpoint to create a new Kanban board
@app.route('/create_board', methods=['POST'])
def create_board():
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    data = request.get_json()
    name = data.get('name')

    user_id = session['user_id']

    # Create the new board
    new_board = KanbanBoard(name=name)
    db.session.add(new_board)
    db.session.commit()

    # Add default columns to the new board
    default_columns = ['To-Do', 'In Progress', 'Done']
    for column_name in default_columns:
        new_column = KanbanColumn(name=column_name, board_id=new_board.id)
        db.session.add(new_column)

    db.session.commit()

    # Fetch the newly created board with columns and tasks
    new_board = KanbanBoard.query.filter_by(id=new_board.id).first()
    columns_data = [{"id": column.id, "name": column.name, "tasks": []} for column in new_board.columns]
    board_data = {"id": new_board.id, "name": new_board.name, "columns": columns_data}

    return jsonify({"message": "Board created successfully", "board": board_data})

# API endpoint to delete a board and its associated columns and tasks
@app.route('/delete_board/<int:board_id>', methods=['DELETE'])
def delete_board(board_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    # Get the board and its associated columns
    board = KanbanBoard.query.filter_by(id=board_id).first()
    if not board:
        return jsonify({"error": "Board not found"}), 404

    columns = KanbanColumn.query.filter_by(board_id=board_id).all()

    # Delete all tasks associated with the columns
    for column in columns:
        Task.query.filter_by(column_id=column.id).delete()

    # Delete the columns
    KanbanColumn.query.filter_by(board_id=board_id).delete()

    # Delete the board
    db.session.delete(board)
    db.session.commit()

    return jsonify({"message": "Board and associated data deleted successfully"})

# API endpoint to add a new task to a column
@app.route('/add_task/<int:board_id>/<int:column_id>', methods=['POST'])
def add_task(board_id, column_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    data = request.get_json()
    content = data.get('content')

    task = Task(content=content, column_id=column_id)
    db.session.add(task)
    db.session.commit()

    # Fetch the updated board with columns and tasks
    board = KanbanBoard.query.filter_by(id=board_id).first()
    columns_data = [{"id": column.id, "name": column.name, "tasks": [{"id": task.id, "content": task.content} for task in column.tasks]} for column in board.columns]
    board_data = {"id": board.id, "name": board.name, "columns": columns_data}

    return jsonify({"message": "Task added successfully", "board": board_data})

# API endpoint to move a task to a different column
@app.route('/move_task/<int:task_id>/<int:target_column_id>', methods=['POST'])
def move_task(task_id, target_column_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    task = Task.query.filter_by(id=task_id).first()
    task.column_id = target_column_id
    db.session.commit()

    return jsonify({"message": "Task moved successfully"})

# API endpoint to delete a task
@app.route('/delete_task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    task = Task.query.filter_by(id=task_id).first()
    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": "Task deleted successfully"})

# API endpoint to update task content
@app.route('/update_task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()
    new_content = data.get('content')

    task.content = new_content
    db.session.commit()

    return jsonify({"message": "Task updated successfully"})



# User logout endpoint
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Successfully logged out", "redirect": url_for('serve_login')})

# Serve the login page
@app.route('/login')
def serve_login():
    return render_template('login.html')

# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hashed_password = generate_password_hash(password, 'scrypt', 16)
    new_user = User(username=username, password_hash=hashed_password, profile_picture='default_profile.png')

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})


# User login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({"message": "Login successful", "redirect": url_for('serve_dashboard')})
    else:
        return jsonify({"error": "Invalid username or password"}), 401


# User dashboard endpoint
@app.route('/dashboard')
def serve_dashboard():
    # Check if the user is authenticated
    if 'user_id' not in session:
        # If not authenticated, redirect to the login page
        return redirect(url_for('serve_login'))
    else:
        # Render the dashboard.html template with the boards data
        return render_template('dashboard.html')

# Add a new route to serve boards data in JSON format
@app.route('/dashboard-data')
def get_dashboard_data():
    # Check if the user is authenticated
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    # If authenticated, fetch boards for the logged-in user
    user_boards = KanbanBoard.query.all()

    # Prepare the data to be sent to the frontend
    boards_data = []
    for board in user_boards:
        columns_data = []
        for column in board.columns:
            tasks_data = [{"id": task.id, "content": task.content} for task in column.tasks]
            columns_data.append({"id": column.id, "name": column.name, "tasks": tasks_data})

        boards_data.append({"id": board.id, "name": board.name, "columns": columns_data})

    return jsonify({"boards_data": boards_data})

# Define the directory where profile pictures will be stored
PROFILE_PICTURES_DIR = 'static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if the uploaded file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API endpoint to update the user's profile picture
@app.route('/update_profile_picture', methods=['POST'])
def update_profile_picture():
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Check if the POST request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # Check if the user submitted an empty file field
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check if the file is an allowed type
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    # Save the uploaded file with a secure filename
    filename = secure_filename(file.filename)
    file_path = os.path.join(PROFILE_PICTURES_DIR, filename)
    file.save(file_path)

    # Update the user's profile picture filename in the database
    user.profile_picture = filename
    db.session.commit()

    return jsonify({"message": "Profile picture updated successfully"})

# ... (existing code)

# Serve uploaded profile pictures
@app.route('/profile_pictures/<filename>')
def profile_picture(filename):
    return send_from_directory(PROFILE_PICTURES_DIR, filename)

@app.route('/user-data', methods=['GET'])
def get_user_data():
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Fetch boards data for the user
    user_boards = KanbanBoard.query.all()
    boards_data = []
    for board in user_boards:
        columns_data = []
        for column in board.columns:
            tasks_data = [{"id": task.id, "content": task.content} for task in column.tasks]
            columns_data.append({"id": column.id, "name": column.name, "tasks": tasks_data})

        boards_data.append({"id": board.id, "name": board.name, "columns": columns_data})

    user_data = {
        "id": user.id,
        "username": user.username,
        "profile_picture" : user.profile_picture
    }

    return jsonify({"user_data": user_data, "boards_data": boards_data})

@app.route('/')
def serve_index():
    # Check if the user is authenticated
    if 'user_id' in session:
        # If authenticated, redirect to a different route, e.g., '/dashboard'
        return redirect(url_for('login'))

    # If not authenticated, render the index.html template
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
