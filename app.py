from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import openpyxl

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///violations.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    license_plate = db.Column(db.String(20), nullable=False)
    violation = db.Column(db.String(200), nullable=False)
    violation_date = db.Column(db.DateTime, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    search = request.args.get('search')
    if search:
        violations = Violation.query.filter(
            Violation.name.contains(search) |
            Violation.license_plate.contains(search)
        ).all()
    else:
        violations = Violation.query.all()
    return render_template('index.html', violations=violations)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_violation():
    if request.method == 'POST':
        name = request.form['name']
        birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
        address = request.form['address']
        license_plate = request.form['license_plate']
        violation = request.form['violation']
        violation_date = datetime.strptime(request.form['violation_date'], '%Y-%m-%dT%H:%M')
        
        new_violation = Violation(
            name=name,
            birth_date=birth_date,
            address=address,
            license_plate=license_plate,
            violation=violation,
            violation_date=violation_date
        )
        db.session.add(new_violation)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_violation(id):
    violation = Violation.query.get(id)
    if request.method == 'POST':
        violation.name = request.form['name']
        violation.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d').date()
        violation.address = request.form['address']
        violation.license_plate = request.form['license_plate']
        violation.violation = request.form['violation']
        violation.violation_date = datetime.strptime(request.form['violation_date'], '%Y-%m-%dT%H:%M')
        
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('edit.html', violation=violation)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_violation(id):
    violation = Violation.query.get(id)
    if violation:
        db.session.delete(violation)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('manage_users'))
    return render_template('add_user.html')

@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    user = User.query.get(id)
    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']:
            user.set_password(request.form['password'])
        db.session.commit()
        return redirect(url_for('manage_users'))
    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/test_route')
@login_required
def test_route():
    return "Route hoạt động!"

@app.route('/export_excel')
@login_required
def export_excel():
    violations = Violation.query.all()
    data = [{
        'Họ tên': v.name,
        'Ngày tháng năm sinh': v.birth_date,
        'Địa chỉ': v.address,
        'Biển số xe': v.license_plate,
        'Lỗi vi phạm': v.violation,
        'Ngày giờ vi phạm': v.violation_date
    } for v in violations]

    file_path = os.path.join(os.path.expanduser("~"), "Downloads", "violations.xlsx")
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    # Write headers
    headers = ['Họ tên', 'Ngày tháng năm sinh', 'Địa chỉ', 'Biển số xe', 'Lỗi vi phạm', 'Ngày giờ vi phạm']
    sheet.append(headers)

    # Write data
    for row_data in data:
        sheet.append([
            row_data['Họ tên'],
            row_data['Ngày tháng năm sinh'].strftime('%Y-%m-%d'),
            row_data['Địa chỉ'],
            row_data['Biển số xe'],
            row_data['Lỗi vi phạm'],
            row_data['Ngày giờ vi phạm'].strftime('%Y-%m-%d %H:%M:%S')
        ])

    workbook.save(file_path)

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)