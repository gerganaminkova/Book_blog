import os
import hashlib
from datetime import date
from functools import wraps
from unittest import result
from forms import CommentForm
from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text
from forms import CreateBookPostReview, RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, abort, render_template, redirect, url_for, flash
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

@app.template_filter('gravatar')
def gravatar(email, size=100, rating='g', default='retro'):
    if not email:
        email = ""
    email_hash = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}&r={rating}"

app.jinja_env.globals['gravatar'] = gravatar

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI','sqlite:///posts.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(230), nullable=False)
    name = db.Column(db.String(30), nullable=False)
    posts = relationship("BookPostReview", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")

class BookPostReview(db.Model):
    __tablename__ = "book_reviews"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    book_title = db.Column(db.String(30), nullable=False)
    book_author = db.Column(db.String(30), nullable=False)
    genre = db.Column(db.String(30), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    cover_url = db.Column(db.String(250), nullable=False)
    review = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("book_reviews.id"))
    parent_post = relationship("BookPostReview", back_populates="comments")


with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function




@app.route('/register',methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=7
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html",form=form)


@app.route('/login',methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for("get_all_posts"))

    return render_template("login.html", form = form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(
        db.select(BookPostReview)
        .order_by(BookPostReview.rating.desc())
        .limit(3))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BookPostReview, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text = comment_form.comment.data,
            comment_author = current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post",post_id=post_id))
    return render_template("post.html", post=requested_post,form=comment_form)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreateBookPostReview()
    if form.validate_on_submit():
        new_post = BookPostReview(
            book_title=form.book_title.data,
            book_author=form.book_author.data,
            genre=form.genre.data,
            rating=form.rating.data,
            pages=form.pages.data,
            cover_url=form.cover_url.data,
            review=form.review.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("all_book_reviews"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BookPostReview, post_id)
    edit_form = CreateBookPostReview(
        book_title=post.book_title,
        book_author=post.book_author,
        genre=post.genre,
        rating=post.rating,
        pages=post.pages,
        cover_url=post.cover_url,
        review=post.review
    )
    if edit_form.validate_on_submit():
        post.book_title = edit_form.book_title.data
        post.book_author = edit_form.book_author.data
        post.genre = edit_form.genre.data
        post.rating = edit_form.rating.data
        post.pages = edit_form.pages.data
        post.cover_url = edit_form.cover_url.data
        post.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BookPostReview, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('all_book_reviews'))


@app.route("/reading-next")
def reading_next():
    return render_template("reading_next.html")

@app.route("/all_book_reviews")
def all_book_reviews():
    result = db.session.execute(
        db.select(BookPostReview).order_by(BookPostReview.rating.desc())
    )
    posts = result.scalars().all()
    return render_template("all_book_reviews.html",all_posts=posts)


if __name__ == "__main__":
    app.run(debug=False, port=5002)
