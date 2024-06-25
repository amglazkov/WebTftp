import os
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static', template_folder='/app/webtftp')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)
app.secret_key = 'my key'  # Секретный ключ для безопасности

login_manager = LoginManager()
login_manager.init_app(app)

# Dummy users dictionary for demonstration
users = {'root': {'password': 'password'}}  # Замените это на вашу реальную базу данных пользователей

# User class for Flask-Login
class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return

    user = User()
    user.id = username
    return user

# Check user credentials
def check_user(username, password):
    if username in users and users[username]['password'] == password:
        return True
    return False
@app.route('/opt/flash')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('list_files'))
    else:
        return redirect(url_for('login.html'))
# Обработчик для страницы входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('list_files'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if check_user(username, password):
            user = User()
            user.id = username
            login_user(user)
            return redirect(url_for('list_files'))

    return render_template('login.html')
@app.before_request
def check_user_status():
    if not current_user.is_authenticated and request.endpoint != 'login':
        return redirect(url_for('login'))
#Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
 
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///file_descriptions.db'  # Используем SQLite базу данных
db = SQLAlchemy(app)

class FileDescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
#Добавлен новый код
@app.route('/')
def index():
    files = []
    for filename in sorted(os.listdir(tftp_directory)):
        filepath = os.path.join(tftp_directory, filename)
        if os.path.isfile(filepath):
            file_description = FileDescription.query.filter_by(filename=filename).first()
            if file_description:
                description = file_description.description
            else:
                description = ''
            files.append({'filename': filename, 'description': description})
    return render_template('index.html', files=files)
@app.route('/add_description/<filename>', methods=['POST'])
def add_description(filename):
    description = request.form.get('description')
    file = FileDescription.query.filter_by(filename=filename).first()
    if file:
        file.description = description
    else:
        new_file = FileDescription(filename=filename, description=description)
        db.session.add(new_file)
    db.session.commit()
    return redirect(url_for('index'))
# Путь к директории, где хранятся файлы TFTP сервера
tftp_directory = '/var/lib/tftpboot'

# Загрузка файла на сервер
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files['file']
    if file:
        filename = file.filename
        file.save(os.path.join(tftp_directory, filename))
        new_file = FileDescription(filename=filename)
        db.session.add(new_file)
        db.session.commit()
    return redirect(url_for('index')) 
# Обработчик для списка файлов
@app.route('/')
def list_files():
    if not current_user.is_authenticated:
        print("User is not authenticated. Redirecting to login page.")
        return redirect(url_for('login'))
 
    files = os.listdir(tftp_directory)
    return render_template('index.html', files=files)
 
# Просмотр содержимого файла
@app.route('/view/<filename>')
@login_required
def view_file(filename):
    file_path = os.path.join(tftp_directory, filename)
    with open(file_path, 'r') as file:
        content = file.read()
    return render_template('view.html', filename=filename, content=content)
 
# Редактирование файла
@app.route('/edit/<filename>', methods=['GET', 'POST'])
@login_required
def edit_file(filename):
    file_path = os.path.join(tftp_directory, filename)
    if request.method == 'POST':
        content = request.form['content']
        with open(file_path, 'w') as file:
            file.write(content)
        return redirect(url_for('list_files'))
    else:
        with open(file_path, 'r') as file:
            content = file.read()
        return render_template('edit.html', filename=filename, content=content)
# Удаление файла
@app.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    file_path = os.path.join(tftp_directory, filename)
    os.remove(file_path)
    return redirect(url_for('list_files'))

if __name__ == '__main__':
    # Создаем базу данных и таблицы. B запускаем приложение, указываем IP и порт
    with app.app_context():
        db.create_all()
    app.run(host='1.1.1.1', port=5000, debug=True)