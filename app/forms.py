from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class UserForm(FlaskForm):
    name = StringField('名前', validators=[DataRequired(), Length(min=3, max=100)])
    password = StringField('パスワード', validators=[DataRequired()])
    submit = SubmitField('送信')
