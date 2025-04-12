from flask import Flask,render_template,request, redirect, url_for # type: ignore
from flask_sqlalchemy import SQLAlchemy
from app.forms import UserForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 任意の秘密のキーを設定(WTForms:フォームバリデーション用)
app.config.from_pyfile('config.py')  # 設定を読み込む
db = SQLAlchemy(app)

# モデル定義（例：User）
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # 名前をユニークに
    password = db.Column(db.String(100), unique=False, nullable=False)

    def __repr__(self):
        return f'<User {self.name}>'


@app.route("/")
def hello():
    return "hello world"

#CRUD
#C
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    form = UserForm()

    if form.validate_on_submit():
        user = User(name=form.name.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('users'))

    return render_template('add_user.html', form=form)

#R
@app.route("/users")
def users():
    users = User.query.all()
    return render_template("users.html", users=users)

#U
@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        user.name = request.form['name']
        user.password = request.form['password']
        db.session.commit()
        return redirect(url_for('users'))
    
    return render_template('edit_user.html', user=user)

#D
@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('users'))


#userの詳細ページ
@app.route('/user/<int:id>')
def user_detail(id):
    user = User.query.get_or_404(id)
    return render_template('user_detail.html', user=user)


@app.route("/index")
def index():
    return render_template("index.html")
