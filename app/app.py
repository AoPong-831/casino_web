from flask import Flask,render_template,request,redirect,url_for # type: ignore
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from flask import Response#csv用
import csv#csv用
from io import TextIOWrapper#csv用
from datetime import datetime#ログイン機能用
from flask import session#ログイン機能用

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
    name = db.Column(db.String(20),nullable=False, unique = True)
    pw = db.Column(db.String(20), nullable=False)
    chip = db.Column(db.Integer)
    point = db.Column(db.Integer)
    last_login = db.Column(db.Date)#年月日だけでいいのでData型。時間まで欲しい場合はDatetime
    #login_date = ...

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(20), nullable=False)#ーザ登録チケット発行時はname置き場に代用
    value = db.Column(db.Integer, nullable=False)
    user_pw = db.Column(db.String(20), nullable = True)#ユーザ登録チケット発行時のpw置き場

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
        #チケット発行
        type = "add_user"
        category = request.form["name"]#categoryをname入れに代用
        user_pw = request.form["pw"]
        ticket = Ticket(user_id=1,type=type,category=category,value=0,user_pw=user_pw)
        db.session.add(ticket)
        db.session.commit()
        return render_template("stanby_add_user.html")
    return render_template("add_user.html")

# --- ランキング表示 ---
@app.route('/ranking')
@login_required
def ranking():
    users = User.query.order_by(User.chip.desc()).all()#usersをchipで降順(desc){昇順はasc}
    return render_template("ranking.html",users=users,current_user=current_user)

# --- ユーザ削除 ---
@app.route('/delete_user/<int:id>', methods=["GET",'POST'])
@login_required
def delete_user(id):
    if request.method == "POST":
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('ranking'))
    return render_template("delete_user.html",user=User.query.get(id))

# --- ticket追加 ---
@app.route("/ticket_create/<int:id>",methods=["GET","POST"])
@login_required
def ticket_create(id):
    if request.method == "POST":
        type = request.form["type"]
        category = request.form["category"]
        value = request.form["value"]
        ticket = Ticket(user_id=id,type=type,category=category,value=value)
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for("ranking"))
    else:
        user=User.query.get(id)
        return render_template("ticket_create.html",user=user)

# --- ticket一覧 ---
@app.route("/ticket_all")
@login_required
def ticket_all():
    if current_user.id != 1:#rootユーザでないときアクセス拒否
        return "403 Forbidden<br> アクセスが拒否されました。<br> [原因]<br> アカウントにアクセス権限がありません。"

    tickets = Ticket.query.all()
    #ticket.user_id の user.name をhtmlで表示するために、User の name だけをdictionary型で作成
    user_dict = {user.id: user.name for user in User.query.all()}
    return render_template("ticket_all.html",tickets=tickets,user_dict=user_dict)

# --- ticket受付 ---
@app.route("/ticket_receive/<int:id>",methods=["GET","POST"])
@login_required
def ticket_receive(id):
    ticket = Ticket.query.get(id)
    user = User.query.get(ticket.user_id)

    if request.method == "POST":
        if ticket.type == "withdrawal":#引出
            if ticket.category == "chip":
                user.chip = user.chip - ticket.value
            elif ticket.category == "point":
                user.point = user.point - ticket.value
        elif ticket.type == "deposit":#預入
            if ticket.category == "chip":
                user.chip = user.chip + ticket.value
            elif ticket.category == "point":
                user.point = user.point + ticket.value
        elif ticket.type == "add_user":#アカウント作成
            name = ticket.category
            pw = ticket.user_pw
            #DBに書き込む
            user = User(name=name,pw=pw,chip=500,point=0,last_login=datetime.now().date())
            db.session.add(user)
            db.session.commit()
        else:
            return "ticket.type or category エラー"
        db.session.commit()
        delete_ticket(ticket.id)#ticket削除処理
        return redirect(url_for("ticket_all"))
    else:
        name = user.name
        return render_template("ticket_receive.html",ticket=ticket,user=user,name=name)

# --- ticket削除 ---
@app.route('/delete_ticket/<int:id>', methods=['POST'])
@login_required
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return redirect(url_for("ticket_all"))

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

# --- チップ交換 ---
@app.route("/exchange/<int:id>", methods=["GET",'POST'])
@login_required
def exchange(id):
    user = User.query.get(id)
    message = ""

    if request.method == "POST":
        input_point = int(request.form["point"])#入力された交換するポイント量
        if user.point >= input_point:
            user.point = user.point - input_point#ポイント引き
            user.chip = user.chip + (input_point//10)#チップ追加
            user.point = user.point + (input_point%10)#チップ交換のおつり

            db.session.commit()
            return redirect(url_for("ranking"))
        else:
           message="[ERROR]ポイント不足"
    return render_template("exchange.html",user=user,message=message)



# --- ログイン(初期ルート) ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"]
        pw = request.form["pw"]
        user = User.query.filter_by(name=name, pw=pw).first()#初めにヒットするデータを取得
        if user:
            user.last_login = datetime.now().date()#ログイン最終日付更新(時間もいる場合は.date()を消す)
            db.session.commit()

            login_user(user)#ログイン状態に
            return redirect(url_for("ranking"))
        else:
            return "ログイン失敗"
    return render_template("login.html")

# --- ログアウト ---
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# --- CSV_インポート ---
@app.route("/import_users", methods=["GET","POST"])
def import_users():
    if request.method == 'POST':
        file = request.files['file']
        if not file or not file.filename.endswith('.csv'):
            return "CSVファイルを選んでください"

        # CSV読み込み
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)

        for row in reader:#行毎に行う
            name = row.get('name')
            pw = row.get('pw')
            chip = row.get('chip')
            point = row.get('point')
            #last_login = ... xxxx-xx-xxの文字列をdate型に変換。※不正な文字列の場合、エラーの原因になる。
            last_login = datetime.strptime(row.get('last_login'),"%Y-%m-%d").date()
            if name and pw and chip and point and last_login:#空白がなければ
                user = User(name=name, pw=pw, chip=chip, point=point, last_login=last_login)
                db.session.add(user)

        db.session.commit()
        return redirect(url_for('ranking'))  # 任意の表示先へ

    return render_template('import_users.html')

# --- CSV_エクスポート ---
@app.route('/export_users')
def export_users():
    users = User.query.all()

    def generate():#この関数で逐次的にcsv文字列を生成
        yield 'name,pw,chip,point,last_login\n'  # CSVヘッダー
        for user in users:
            yield f'{user.name},{user.pw},{user.chip},{user.point},{user.last_login}\n'

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users.csv'}
    )