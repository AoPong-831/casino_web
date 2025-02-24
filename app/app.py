from flask import Flask,render_template # type: ignore

app = Flask(__name__)

@app.route("/")
def hello():
    return "hello world"

@app.route("/index")
def index():
    return render_template("index.html")
