from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, BlankForm
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)
app.app_context().push()
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///authentication_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False


connect_db(app)

toolbar = DebugToolbarExtension(app)


@app.route("/")
def index():
    """Redirects to the register page."""
    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Allows user to register."""
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        db.session.commit()
        session["username"] = new_user.username
        return redirect(f"/users/{session['username']}")
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_user():
    """Allows user to login on created page."""

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            session["username"] = user.username
            return redirect(f"/users/{session['username']}")
        else:
            form.username.errors = ["Invalid username/password"]
            flash("Please login to your account to see our secret page!", "danger")
            return redirect("/login")
    return render_template("login.html", form=form)


@app.route("/users/<username>")
def user_page(username):
    """Shows user's information page."""
    if "username" not in session or username != session["username"]:
        raise Unauthorized()

    user = User.query.get(username)
    form = BlankForm()
    return render_template("show.html", user=user, form=form)


@app.route("/logout")
def logout():
    """Allows user to log out."""
    session.pop("username")
    flash("Goodbye!")
    return redirect("/")


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    """Allows user to delete his account."""
    if "username" not in session or username != session["username"]:
        raise Unauthorized()

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")
    return redirect("/")


@app.route("/users/<username>/feedback/add", methods=["GET", "POST"])
def add_feedback(username):
    """Allows user to add personal feedback to the page."""
    if "username" not in session or username != session["username"]:
        raise Unauthorized()

    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        new_feedback = Feedback(title=title, content=content, username=username)
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(f"/users/{new_feedback.username}")
    else:
        return render_template("new_feedback.html", form=form)


@app.route("/feedback/<int:id>/update", methods=["GET", "POST"])
def update_feedback(id):
    """Allows user to edit previously created feedback."""
    feedback = Feedback.query.get(id)

    if "username" not in session or feedback.username != session["username"]:
        raise Unauthorized()

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("edit_feedback.html", form=form, feedback=feedback)


@app.route("/feedback/<int:id>/delete", methods=["POST"])
def delete_feedback(id):
    """Allows user to delete previously created feedback."""

    feedback = Feedback.query.get(id)
    if "username" not in session or feedback.username != session["username"]:
        raise Unauthorized()

    form = BlankForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")
