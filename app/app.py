from flask import Flask,render_template,request, redirect, url_for # type: ignore
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('config.py')  # 設定を読み込む
db = SQLAlchemy(app)

# モデル定義（例：User）
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.name}>'

@app.route("/")
def hello():
    return "hello world"

@app.route("/users")
def users():
    users = User.query.all()
    return render_template("users.html", users=users)

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        
        # 新しいユーザーをデータベースに追加
        user = User(name=name, password=password)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('users'))
    return render_template('add_user.html')


@app.route("/index")
def index():
    return render_template("index.html")
