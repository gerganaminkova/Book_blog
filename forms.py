from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms.fields import choices
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, URL, Email
from wtforms import StringField, SubmitField, PasswordField


# WTForm for creating a book review
class CreateBookPostReview(FlaskForm):
    book_title = StringField("Book Title", validators=[DataRequired()])
    book_author = StringField("Book Author", validators=[DataRequired()])
    genre = StringField("Genre", validators=[DataRequired()])
    rating = SelectField("Rating",
                         choices=[(1, "★☆☆☆☆"),
                                   (2, "★★☆☆☆"), (3, "★★★☆☆"),
                                   (4, "★★★★☆"), (5, "★★★★★")],
                         coerce=int, validators=[DataRequired()])
    pages = IntegerField("Pages", validators=[DataRequired()])
    cover_url = StringField("Cover URL", validators=[DataRequired(), URL()])
    review = CKEditorField("Review", validators=[DataRequired()])
    submit = SubmitField("Save book")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class CommentForm(FlaskForm):
    comment = StringField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
