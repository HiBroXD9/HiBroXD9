import json
import pprint
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todolist.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

with app.app_context():
    db.create_all()

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    postponed = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Task {self.title}>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username = username).first_or_404()

        print("user selectat")
        pprint.pprint(user)
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = username

            flash('Te-ai logat cu succes!', 'success')

            return redirect(url_for('index'))
        else:
            flash('Date invalide. Încearcă din nou.', 'danger')
    return render_template('login.html')

@app.route('/inregistrare', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    return render_template('inregistrare.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Te-ai deconectat.', 'success')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    tasks = Task.query.filter_by(user_id=session['user_id']).all()

    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    title = request.form.get('title')
    if title:
        new_task = Task(title=title, user_id=session['user_id'])
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/postpone/<int:task_id>', methods=['POST'])
def postpone_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    task.postponed = True
    db.session.commit()
    
    delayed_tasks = Task.query.filter_by(postponed=True).all()
    return render_template('Amanate.html', tasks=delayed_tasks)



@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    task = Task.query.get_or_404(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for('completed_tasks'))

@app.route('/completed')
def completed_tasks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    tasks = Task.query.filter_by(user_id=session['user_id'], completed=True).all()
    return render_template('completed.html', tasks=tasks)

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        task.title = request.form['title']
        db.session.commit()
        flash('Sarcina a fost actualizată cu succes!', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit.html', task=task)

@app.route('/generate_password', methods=['GET', 'POST'])
def generate_password():
    if request.method == 'POST':
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        return f'Parola: {hashed_password}'
    return render_template('generate_password.html')

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
