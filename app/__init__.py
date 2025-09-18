from flask import Flask,render_template,request,redirect,url_for # type: ignore
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from flask_migrate import Migrate
from flask import session#ログイン機能用
from werkzeug.utils import secure_filename#日程表_画像読み込み用(危険なファイル名{../../}などを除去する)

#DBとマイグレート初期化
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    #Flaskアプリ作成
    app = Flask(__name__)
    
    #FLASK_ENV 依存でPostgreSQL or SQLite を選択。DATABASE_URLがないと接続失敗の可能性あり。
    #ただし、元コードではFLASK_ENVに依存しない分、DATABASE_URLを取得できなければweb上でもSQLiteを使ってしまう欠点がある。
    if os.getenv("FLASK_ENV") == "production":
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    #(元のコード)app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
    
    
    #Heroku では postgres:// を postgresql:// に変換 ⇒ SQLAlchemy が PostgreSQL接続を認識できるようになる
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "your-secret-key" #これないとエラー出るらしい

    #初期化(???)
    db.init_app(app)
    migrate.init_app(app,db)
    login_manager.init_app(app)

    # モデルを必ずインポートして Alembic に認識させる(???)
    #⇒インポートはここでする。(循環を避けるため関数内で)
    with app.app_context():#★ app context 内でモデルを読み込み
        from app import models
    
    #DBの追加はここでは？
    from app.models import User#

    # user_loaderをここに書く(???)
    #ユーザー読み込み関数
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ルート登録(???)
    from app import routes
    app.register_blueprint(routes.bp)#これでがっちゃんこらしい

    return app