#DBモデル
from flask_login import UserMixin
from app import db

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
    icon = db.Column(db.String(200), default="icons/default.png")#アイコン

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