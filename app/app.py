from flask import Flask,render_template,request,redirect,url_for # type: ignore
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.secret_key = "your-secret-key" #これないとエラー出るらしい

#環境変数から DATABASE_URL を取得(Herokuでは自動設定される)
DATABASE_URL = os.getenv("postgres://u9ksot7i4tclrr:p325c32f4abfd8f0f9da40ccaba8d89d36f548b07d6c6021421d78b1c30b3dd07@ce0lkuo944ch99.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dfa72fs3dgt167")

#ローカルで開発する場合のフォールバック
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///local.db" #SQLiteを使う

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#DBインスタンス作成
db = SQLAlchemy(app)

#ログイン管理
login_manager = LoginManager()
login_manager.init_app(app)

# --- モデル定義 ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    pw = db.Column(db.Integer, nullable=False)
    point = db.Column(db.Integer)
    #login_date = ...

#ユーザー読み込み関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        pw = request.form["pw"]
        
        #DBに書き込む
        user = User(name=name,pw=pw,point=0)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("ranking"))
    return render_template("add_user.html")

# --- 削除機能 ---
@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('ranking'))


# --- ランキング表示 ---
@app.route('/ranking')
@login_required
def ranking():
    users = User.query.all()
    return render_template("ranking.html",users=users)

# --- user画面 ---
@app.route("/profile/<int:id>")
@login_required
def profile(id):
    #自分の画面以外見れない
    if current_user.id != id:
        return "アカウントが違うよ！"
    else:
        pass
    return render_template("profile.html",user=User.query.get(id))

# --- 初期ルート ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(name=request.form["name"]).first()
        if user and user.pw == request.form["pw"]:
            login_user(user)
            return redirect(url_for("ranking"))
        return "ログイン失敗"
    return render_template("login.html")

# --- ログアウト ---
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))