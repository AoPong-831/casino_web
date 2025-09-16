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
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///app.db")
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
    
    from app.models import User#login_manager用

    # user_loaderをここに書く(???)
    #ユーザー読み込み関数
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ルート登録(???)
    from app import routes
    app.register_blueprint(routes.bp)#これでがっちゃんこらしい

    return app