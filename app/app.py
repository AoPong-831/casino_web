from flask import Flask,render_template,request,redirect,url_for # type: ignore
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from flask import Response#csv用
import csv#csv用
from io import TextIOWrapper#csv用
from datetime import datetime#ログイン機能用
from flask import session#ログイン機能用
from werkzeug.utils import secure_filename#日程表_画像読み込み用(危険なファイル名{../../}などを除去する)

app = Flask(__name__)
app.secret_key = "your-secret-key" #これないとエラー出るらしい

#環境変数から DATABASE_URL を取得(Herokuでは自動設定される)
DATABASE_URL = os.getenv("postgres://u9ksot7i4tclrr:p325c32f4abfd8f0f9da40ccaba8d89d36f548b07d6c6021421d78b1c30b3dd07@ce0lkuo944ch99.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dfa72fs3dgt167")

#ローカルで開発する場合のフォールバック
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///local.db" #SQLiteを使う

# 許可する拡張子(日程表用)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
#日程表を保存するpath
UPLOAD_FOLDER = "app/static/images"

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER#日程表の保存pathをコンフィグに設定(日程表用)

#DBインスタンス作成
db = SQLAlchemy(app)

#ログイン管理
login_manager = LoginManager()
login_manager.init_app(app)

# --- モデル定義 ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20),nullable=False, unique = True)
    username = db.Column(db.String(20),nullable=False, unique = True)
    pw = db.Column(db.String(20), nullable=False)
    chip = db.Column(db.Integer)
    point = db.Column(db.Integer)
    last_login = db.Column(db.Date)#年月日だけでいいのでData型。時間まで欲しい場合はDatetime
    station = db.Column(db.String(20))#最寄り駅
    fare = db.Column(db.Integer)#大宮駅までの運賃

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(20), nullable=False)#月初めボーナスは"monthly_bonus"
    value = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(20), nullable = True)#ユーザ登録チケット発行時のname置き場
    user_username = db.Column(db.String(20), nullable = True)#ユーザ登録チケット発行時のusername置き場
    user_pw = db.Column(db.String(20), nullable = True)#ユーザ登録チケット発行時のpw置き場

class Chip_log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(20))
    chip_before = db.Column(db.Integer, nullable=False)
    chip_after = db.Column(db.Integer, nullable=False)
    point_before = db.Column(db.Integer, nullable=False)
    point_after = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date)#年月日だけでいいのでData型。時間まで欲しい場合はDatetime

#ユーザー読み込み関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Chip_Log記載
def update_chip_Log(user):#userのchip,pointの変更時 and ログイン時に実行する関数
    today = datetime.now().date()#今日の日付を取得
    chip_logs = Chip_log.query.filter(Chip_log.date == today,Chip_log.user_id == user.id).all()#今日更新したデータ & user.idが一致したものを抽出

    is_Flag = False#userが記録された場合のフラグ
    for log in chip_logs:
        if log.user_id == user.id:#user.idが一致する場合(logに値があれば、一致するはず)、更新
            log.chip_after = user.chip
            log.point_after = user.point
            is_Flag = True#userが記録された場合のフラグ
            break
        else:
            pass#次のユーザ判定へ

    if not(is_Flag):#今日初更新の場合(ログイン時を想定)
        chip_log = Chip_log(user_id=user.id,user_name=user.name,chip_before=user.chip,chip_after=user.chip,point_before=user.point,point_after=user.point,date=datetime.now().date())
        db.session.add(chip_log)
        is_Flag = True#userが記録された場合のフラグ

    db.session.commit()
    return

# --- ユーザー追加(リンク直以外でアクセス禁止) ---
@app.route('/add_user', methods=["GET","POST"])
def add_user():
    if request.method == "POST":
        #チケット発行
        type = "add_user"
        user_name = request.form["name"]
        user_username = request.form["username"]
        user_pw = request.form["pw"]
        ticket = Ticket(user_id=1,type=type,category="",value=500,user_name=user_name,user_username=user_username,user_pw=user_pw,)
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

# --- ユーザーname変更 ---
@app.route('/change_user_name/<int:id>', methods=["GET","POST"])
def change_name_user(id):
    if current_user.id != 1:#rootユーザでないときアクセス拒否
        return "403 Forbidden<br> アクセスが拒否されました。<br> [原因]<br> アカウントにアクセス権限がありません。"

    if request.method == "POST":
        user = User.query.get(id)
        user.name = request.form["name"]
        db.session.commit()
        return redirect(url_for("ranking"))
    return render_template("change_user_name.html", user=User.query.get(id))

# --- ユーザーusername変更 ---
@app.route('/change_user_username/<int:id>', methods=["GET","POST"])
def change_username_user(id):
    #自分の画面以外見れない
    if current_user.id == 1:
        pass
    elif current_user.id != id:
        return "<h1>アカウントが違うよ！<h1>"
    else:
        pass

    if request.method == "POST":
        user = User.query.get(id)
        user.username = request.form["username"]
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("change_user_username.html", user=User.query.get(id))

# --- ユーザーPW変更 ---
@app.route('/change_user_pw/<int:id>', methods=["GET","POST"])
def change_pw_user(id):
    #自分の画面以外見れない
    if current_user.id == 1:
        pass
    elif current_user.id != id:
        return "<h1>アカウントが違うよ！<h1>"
    else:
        pass

    if request.method == "POST":
        user = User.query.get(id)
        user.pw = request.form["pw"]
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("change_user_pw.html", user=User.query.get(id))

# --- ユーザーstation変更 ---
@app.route('/change_user_station/<int:id>', methods=["GET","POST"])
def change_pw_station(id):
    #自分の画面以外見れない
    if current_user.id == 1:
        pass
    elif current_user.id != id:
        return "<h1>アカウントが違うよ！<h1>"
    else:
        pass

    if request.method == "POST":
        user = User.query.get(id)
        user.station = request.form["station"]
        user.fare = request.form["fare"]
        db.session.commit()
        return redirect(url_for("ranking"))
    return render_template("change_user_station.html", user=User.query.get(id))

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

# --- ticket追加(chip, point) ---
@app.route("/ticket_create_chip/<int:id>",methods=["GET","POST"])
@login_required
def ticket_create_chip(id):
    #自分の画面以外見れない
    if current_user.id == 1:
        pass
    elif current_user.id != id:
        return "<h1>アカウントが違うよ！<h1>"
    else:
        pass

    if request.method == "POST":
        type = request.form["type"]
        value = int(request.form["value"])

        #マイナス引出チェック
        user = User.query.get(id)
        if type == "withdrawal":
            if user.chip < value:
                message="[ERROR]chip不足"
                return render_template("ticket_create_chip.html",user=user, message=message)
        
        ticket = Ticket(user_id=id,type=type,category="chip",value=value)
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for("profile", id=current_user.id))
    else:
        user=User.query.get(id)
        return render_template("ticket_create_chip.html",user=user)

@app.route("/ticket_create_point/<int:id>",methods=["GET","POST"])
@login_required
def ticket_create_point(id):
    #自分の画面以外見れない
    if current_user.id == 1:
        pass
    elif current_user.id != id:
        return "<h1>アカウントが違うよ！<h1>"
    else:
        pass

    if request.method == "POST":#預入オンリーの想定
        value = int(request.form["value"])
       
        ticket = Ticket(user_id=id,type="deposit",category="point",value=value)
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for("profile", id=current_user.id))
    else:
        user=User.query.get(id)
        return render_template("ticket_create_point.html",user=user)

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
    if current_user.id != 1:#rootユーザでないときアクセス拒否
        return "403 Forbidden<br> アクセスが拒否されました。<br> [原因]<br> アカウントにアクセス権限がありません。"
    
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
            name = ticket.user_name
            username = ticket.user_username
            pw = ticket.user_pw
            chip = ticket.value#チケット発行時に500を指定
            #DBに書き込む
            user = User(name=name,username=username,pw=pw,chip=chip,point=0,last_login=datetime.now().date(),station="None",fare=0)
            db.session.add(user)
        elif ticket.type == "monthly_bonus":#月初めボーナス
            pass#チップ直渡しのため処理不要
        elif ticket.type == "fare_bonus":#交通費ボーナス
            user.point = user.point + user.fare
        else:
            return "ticket.type or category エラー"
        
        db.session.commit()
        delete_ticket(ticket.id)#ticket削除処理
        update_chip_Log(user)#Logを記載する関数
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

    if current_user.id == 1:#JackPotの場合は、チケット一覧へ
        return redirect(url_for("ticket_all"))
    return redirect(url_for("profile", id=current_user.id))#他ユーザはプロフィールへ

# --- user画面 ---
@app.route("/profile/<int:id>")
@login_required
def profile(id):
    user=User.query.get(id)
    tickets = Ticket.query.filter_by(user_id=id).all()#ユーザの申請中チケットを表示
    chip_logs = Chip_log.query.filter(Chip_log.user_id == user.id).all()#cjip_logデータを抽出
    #profile.html の Chart.js 用に chip_logs のデータを加工
    chips = []#チップのデータ
    points= []#ポイントのデータ
    dates = []#日付のデータ
    for log in chip_logs:
        chips.append(log.chip_before)
        chips.append(log.chip_after)
        points.append(log.point_before)
        points.append(log.point_after)
        str_date = log.date.strftime("%Y/%m/%d")#2025/06/26 の形でstr型に加工。
        dates.append(str_date + "_bf")#before
        dates.append(str_date + "_af")#after

    #自分の画面以外見れない用に！
    if current_user.id == 1 or current_user.id == id:
        return render_template("profile.html",user=user,tickets=tickets,chips=chips,points=points,dates=dates)
    elif current_user.id != id:#該当ユーザ以外はグラフのみ
        return render_template("profile_view.html",user=user,chips=chips,points=points,dates=dates)

# --- チップ交換 ---
@app.route("/exchange/<int:id>", methods=["GET",'POST'])
@login_required
def exchange(id):
    #自分の画面以外見れない
    if current_user.id == 1:
        pass
    elif current_user.id != id:
        return "<h1>アカウントが違うよ！<h1>"
    else:
        pass

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
        username = request.form["username"]
        pw = request.form["pw"]
        user = User.query.filter_by(username=username, pw=pw).first()#初めにヒットするデータを取得
        if user:
            if user.id != 1:#rootユーザでない場合、ボーナス付与の分岐へ
                #月初めボーナス(if 年月が同じなら、何もせず else ボーナス付与)
                if user.last_login.year == datetime.now().year and user.last_login.month == datetime.now().month:
                    pass
                else:
                    if 1000 > (user.chip + (user.point//10)):#総資産100チップ未満
                        value = 300#300ボーナス
                    else:
                        value = 100#100ボーナス

                    ticket = Ticket(user_id=1,type="monthly_bonus",category=user.name,value=value)
                    db.session.add(ticket)
                
                #交通費付与(if 年月日が同じなら、何もせず else 交通費付与)
                if user.last_login == datetime.now().date():
                    pass
                else:
                    ticket = Ticket(user_id=1,type="fare_bonus",category=user.name,value=user.fare)
                    db.session.add(ticket)            
            
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

# --- CSV_インポート_users ---
@app.route("/import_users", methods=["GET","POST"])
def import_users():
    if request.method == 'POST':
        #テーブルの初期化
        db.drop_all()#テーブル削除
        db.create_all() #テーブル作成(テーブル初期化)

        #CSV_インポート
        file = request.files['file']
        if not file or not file.filename.endswith('.csv'):
            return "CSVファイルを選んでください"

        # CSV読み込み
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)

        for row in reader:#行毎に行う
            id = row.get("id")
            name = row.get('name')
            username = row.get('username')
            pw = row.get('pw')
            chip = row.get('chip')
            point = row.get('point')
            #last_login = ... xxxx-xx-xxの文字列をdate型に変換。※不正な文字列の場合、エラーの原因になる。
            last_login = datetime.strptime(row.get('last_login'),"%Y-%m-%d").date()
            station = row.get('station')
            fare = row.get('fare')
            if id and name and username and pw and chip and point and last_login and station and fare:#空白がなければ
                user = User(id = id, name=name, username=username, pw=pw, chip=chip, point=point, last_login=last_login, station=station, fare=fare)
                db.session.add(user)

        db.session.commit()
        return redirect(url_for('ranking'))  #任意の表示先へ

    return render_template('import_users.html')

# --- CSV_エクスポート_users ---
@app.route('/export_users')
def export_users():
    users = User.query.all()

    def generate():#この関数で逐次的にcsv文字列を生成
        yield 'id,name,username,pw,chip,point,last_login,station,fare\n'  # CSVヘッダー
        for user in users:
            yield f'{user.id},{user.name},{user.username},{user.pw},{user.chip},{user.point},{user.last_login},{user.station},{user.fare}\n'

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=users.csv'}
    )

# --- CSV_インポート_lgos ---
@app.route("/import_logs", methods=["GET","POST"])
def import_logs():
    db.session.query(Chip_log).delete()#既に存在するChip_log.dbを削除しないと、idがダブてerror
    db.session.commit()

    if request.method == 'POST':
        #CSV_インポート
        file = request.files['file']
        if not file or not file.filename.endswith('.csv'):
            return "CSVファイルを選んでください"

        # CSV読み込み
        stream = TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)

        for row in reader:#行毎に行う
            id = row.get("id")
            user_id = row.get('user_id')
            user_name = row.get("user_name")
            chip_before = row.get('chip_before')
            chip_after = row.get('chip_after')
            point_before = row.get('point_before')
            point_after = row.get('point_after')
            #last_login = ... xxxx-xx-xxの文字列をdate型に変換。※不正な文字列の場合、エラーの原因になる。
            date = datetime.strptime(row.get('date'),"%Y-%m-%d").date()
            if id and user_id and user_name and chip_before and chip_after and point_before and point_after and date:#空白がなければ
                log = Chip_log(id = id, user_id=user_id, user_name=user_name, chip_before=chip_before, chip_after=chip_after, point_before=point_before, point_after=point_after, date=date)
                db.session.add(log)

        db.session.commit()
        return redirect(url_for('ranking'))  #任意の表示先へ

    return render_template('import_logs.html')

# --- CSV_エクスポート_logs ---
@app.route('/export_logs')
def export_logs():
    logs = Chip_log.query.all()

    def generate():#この関数で逐次的にcsv文字列を生成
        yield 'id,user_id,user_name,chip_before,chip_after,point_before,point_after,date\n'  # CSVヘッダー
        for log in logs:
            yield f'{log.id},{log.user_id},{log.user_name},{log.chip_before},{log.chip_after},{log.point_before},{log.point_after},{log.date}\n'

    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=chip_log.csv'}
    )


# --- 日程表用_拡張子チェック関数 ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 日程表 ---
@app.route("/calendar", methods=["GET","POST"])
def calenar():
    if request.method == 'POST':
        file = request.files["image"]#ファイル受け取り
        if file.filename == '':
            return "ファイルが選択されていません", 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
        return render_template("calendar.html",current_user=current_user)  
    else:#GET
        return render_template("calendar.html",current_user=current_user)


# --- 初期化用ルート（最初だけ使う） ---
@app.route('/initdb_casino')
def init_db():
    db.create_all()  # テーブル作成
    return "DB Initialized"
