from flask import Flask,render_template,request,redirect,url_for # type: ignore
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

#環境変数から DATABASE_URL を取得(Herokuでは自動設定される)
DATABASE_URL = os.getenv("postgres://u9ksot7i4tclrr:p325c32f4abfd8f0f9da40ccaba8d89d36f548b07d6c6021421d78b1c30b3dd07@ce0lkuo944ch99.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dfa72fs3dgt167")

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
    name = db.Column(db.String(20), nullable=False)
    pw = db.Column(db.Integer, nullable=False)
    point = db.Column(db.Integer)
    #login_date = ...

# --- 初期化用ルート (最初だけ使う) ---
@app.route("/initdb")
def init_db():
    db.create_all() #テーブル作成
    return "DB Initialized"

# --- ユーザー追加(リンク直以外でアクセス禁止) ---
@app.route('/add_user', methods=["GET","POST"])
def add_user():
    if request.method == "POST":
        #htmlの入力欄からとってくる値
        name = request.form["name"]
        pw = request.form["birth"]
        
        #DBに書き込む
        user = User(name=name,pw=pw,point=0)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("usres"))
    return render_template("add_user.html")

# --- ランキング表示 ---
@app.route('/ranking')
def ranking():
    users = User.query.all()
    return render_template("ranking.html",users=users)

# --- 以下、自前ルート ---
@app.route("/")
def hello():
    return "Hello World!"

@app.route("/index")
def index():
    return render_template("index.html")