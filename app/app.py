from flask import Flask,render_template # type: ignore
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

#環境変数から DATABASE_URL を取得(Herokuでは自動設定される)
DATABASE_URL = os.getenv("DATABASE_URL")

#ローカルで開発する場合のフォールバック
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///local.db" #SQLiteを使う

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#DBインスタンス作成
db = SQLAlchemy(app)

# --- モデル定義 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

# --- 初期化用ルート (最初だけ使う) ---
@app.route("/initdb")
def init_db():
    db.create_all() #テーブル作成
    return "DB Initialized"

# --- 例：ユーザー追加ルート（簡易） ---
@app.route('/add/<username>')
def add_user(username):
    user = User(name=username)
    db.session.add(user)
    db.session.commit()
    return f"Added {username}"

# --- 確認用ルート ---
@app.route('/users')
def list_users():
    users = User.query.all()
    return '<br>'.join([u.name for u in users])

# --- 以下、自前ルート ---
@app.route("/")
def hello():
    return "Hello World!"

@app.route("/index")
def index():
    return render_template("index.html")