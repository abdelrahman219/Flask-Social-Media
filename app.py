from flask import Flask, g, render_template, flash, redirect, url_for, abort, request


from flask_bcrypt import check_password_hash, generate_password_hash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email
from peewee import DoesNotExist


from models import Friends_list, User, Friendship
import forms
import models


app = Flask(__name__)
app.secret_key = "asdnafnj#46sjsnvd(*$43sfjkndkjvnskb6441531@#$$6sddf"
"""here secret_key is a random string of alphanumerics"""

if __name__ == "__main__":
    app.run(debug=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """Connect to database before each request
    g is a global object, passed around all time in flask, used to setup things which
    we wanna have available everywhere.
    """
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """close all database connection after each request"""
    g.db.close()
    return response


@app.route("/register", methods=("GET", "POST"))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("Congrats, Registered Successfully!", "success")
        models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        return redirect(url_for("index"))
    return render_template("register.html", form=form)


@app.route("/profile_settings", methods=["GET", "POST"])
@login_required
def profile_settings():
    form = forms.ProfileSettingsForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

        # Update the password only if it has been provided
        if form.new_password.data:
            current_user.password = generate_password_hash(form.new_password.data)

        current_user.save()

        flash("Profile settings updated successfully!", "success")
        return redirect(url_for("profile_settings"))

    # Pre-fill the form with the user's current information
    form.username.data = current_user.username
    form.email.data = current_user.email

    return render_template("profile_settings.html", form=form)


@app.route("/login", methods=("GET", "POST"))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password does not match", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                """Creating a session on user's browser"""
                flash("You have been logged in", "success")
                return redirect(url_for("index"))
            else:
                flash("Your email or password does not match", "error")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/new_post", methods=["GET", "POST"])
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        privacy = form.privacy.data

        # Create a new post with the specified privacy option
        models.Post.create(
            user=g.user.id, content=form.content.data.strip(), privacy=privacy
        )

        if privacy == "only_me":
            flash("Post created and set to Only Me privacy.", "success")
            return redirect(url_for("current_all_posts"))
        elif privacy == "friends_only":
            flash("Post created and set to Friends Only privacy.", "success")
            return redirect(url_for("following_posts"))
        else:
            flash("Post created and set to Public privacy.", "success")
            return redirect(url_for("index"))

    return render_template("post.html", form=form)


@app.route("/current_all_posts")
@login_required
def current_all_posts():
    # Retrieve all posts created by the current user
    user = g.user
    posts = (
        models.Post.select()
        .where(models.Post.user == user)
        .order_by(models.Post.timestamp.desc())
    )

    return render_template("current_all_posts.html", posts=posts)


@app.route("/")
@login_required
def index():
    if current_user.is_authenticated:
        # Get the user's friends
        friends = models.Friends_list.select().where(
            models.Friends_list.user == current_user
        )

        # Get the stream of posts from the user's friends
        stream = models.Post.select().where(
            (models.Post.privacy == "public")
            | (
                (models.Post.privacy == "friends_only")
                & (
                    models.Post.user.in_(
                        models.User.select()
                        .join(
                            models.Friends_list,
                            on=(models.User.id == models.Friends_list.friend_id),
                        )
                        .where(models.Friends_list.user == current_user)
                    )
                )
            )
        )
    else:
        # Display only public posts
        stream = models.Post.select().where(models.Post.privacy == "public")

    return render_template("stream.html", stream=stream)


@app.route("/stream")
@app.route("/stream/<username>")
@login_required
def stream(username=None):
    template = "stream.html"
    if username and (current_user.is_anonymous or username != current_user.username):
        try:
            user = models.User.select().where(models.User.username**username).get()
        except models.DoesNotExist:
            abort(404)
        else:
            stream = user.posts.limit(100)
            friends = (
                models.Friends_list.select()
                .where(
                    models.Friends_list.user == current_user,
                    models.Friends_list.friend == user,
                )
                .count()
                > 0
            )
    else:
        stream = current_user.get_stream().limit(100)
        user = current_user
        friends = None  # Set to None since we don't need this information for the current user

    if username:
        template = "user_stream.html"

    return render_template(template, stream=stream, user=user, friends=friends)


@app.route("/following_posts")
@login_required
def following_posts():
    if current_user.is_authenticated:
        # Get the user's friends
        friends = models.Friends_list.select().where(
            models.Friends_list.user == current_user
        )

        # Get the stream of posts from the user's friends
        stream = (
            models.Post.select()
            .where(
                (
                    (models.Post.privacy == "public")
                    & (
                        models.Post.user.in_(
                            models.User.select()
                            .join(
                                models.Friends_list,
                                on=(models.User.id == models.Friends_list.friend_id),
                            )
                            .where(models.Friends_list.user == current_user)
                        )
                    )
                )
                | (
                    (models.Post.privacy == "friends_only")
                    & (
                        models.Post.user.in_(
                            models.User.select()
                            .join(
                                models.Friends_list,
                                on=(models.User.id == models.Friends_list.friend_id),
                            )
                            .where(models.Friends_list.user == current_user)
                        )
                    )
                )
            )
            .where(models.Post.user != current_user)
        )
    else:
        stream = None

    return render_template("following_posts.html", stream=stream, user=current_user)


@app.route("/post/<int:post_id>")
def view_post(post_id):
    posts = models.Post.select().where(models.Post.id == post_id)
    if posts.count() == 0:
        abort(404)
    return render_template("stream.html", stream=posts)


@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    post = models.Post.get_or_none(models.Post.id == post_id)
    if post:
        post.delete_instance()
        flash("Post deleted successfully!", "success")
    else:
        flash("Post not found!", "error")
    return redirect(url_for("current_all_posts"))


@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = models.Post.get_or_none(id=post_id)

    form = forms.EditPostForm()

    if form.validate_on_submit():
        post.content = form.content.data
        post.privacy = form.privacy.data
        post.save()
        flash("Post updated successfully!", "success")
        return redirect(url_for("current_all_posts"))

    form.content.data = post.content
    form.privacy.data = post.privacy

    return render_template("edit_post.html", form=form, post=post)


@app.route("/follow/<username>")
@login_required
def follow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.create(
                from_user=g.user._get_current_object(), to_user=to_user
            )
        except models.IntegrityError:
            pass
        else:
            flash("You are now following {}".format(to_user.username), "success")
    return redirect(url_for("stream", username=to_user.username))


@app.route("/unfollow/<username>")
@login_required
def unfollow(username):
    try:
        to_user = models.User.get(models.User.username**username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.get(
                from_user=g.user._get_current_object(), to_user=to_user
            ).delete_instance()
        except models.IntegrityError:
            pass
        else:
            flash("You have unfollowed {}".format(to_user.username), "success")
    return redirect(url_for("stream", username=to_user.username))


from flask import flash


@app.route("/send_friend_request/<username>")
def send_friend_request(username):
    if current_user.is_authenticated:
        sender = current_user.id
        receiver = models.User.get(models.User.username == username)

        # Check if a friendship record already exists between the sender and receiver
        friendship_exists = (
            models.Friendship.select()
            .where(
                (models.Friendship.sender == sender)
                & (models.Friendship.receiver == receiver)
            )
            .exists()
        )

        if friendship_exists:
            # Friendship request already sent
            flash(
                "You have already sent a friend request to {}".format(
                    receiver.username
                ),
                "error",
            )
        else:
            # Create a Friendship object and save it to the database
            models.Friendship.create(sender=sender, receiver=receiver)

            # Flash a success message
            flash("Friend request sent to {}".format(receiver.username), "success")

        # Redirect to the user's profile page
        return redirect(url_for("stream", username=receiver.username))
    else:
        # Handle the case where the user is not authenticated
        # Redirect to the login page or display an error message
        # ...
        return redirect(url_for("stream", username=receiver.username))


@app.route("/friend_requests")
@login_required
def friend_requests():
    # Fetch the friend requests received by the current user
    friend_requests = models.Friendship.select().where(
        models.Friendship.receiver == current_user,
        models.Friendship.accepted == "pending",
    )

    return render_template("friend_requests.html", friend_requests=friend_requests)


@app.route("/accept_friend_request/<int:id>", methods=["POST"])
@login_required
def accept_friend_request(id):
    # Retrieve the friendship request from the database
    friendship = models.Friendship.get_or_none(
        id=id, receiver=current_user, accepted="pending"
    )
    if friendship:
        # Update the friendship status to accepted
        friendship.accepted = "accepted"
        friendship.save()

        # Create a record in the Friends_list table
        friend = models.Friends_list.create(user=current_user, friend=friendship.sender)
        friend = models.Friends_list.create(user=friendship.sender, friend=current_user)

    return redirect(url_for("friend_requests"))


@app.route("/decline_friend_request/<int:id>", methods=["POST"])
@login_required
def decline_friend_request(id):
    try:
        # Retrieve the friendship request from the database
        friendship = models.Friendship.get(
            id=id, receiver=current_user, accepted="pending"
        )
        # Delete the friendship request
        friendship.delete_instance()
    except DoesNotExist:
        # Handle the case where the friendship request does not exist
        # You can display an error message or handle it as per your requirement
        pass

    return redirect(url_for("friend_requests"))


@app.route("/my_friends")
@login_required
def my_friends():
    # Fetch the friends of the current user from the Friends_list table
    friends = (
        models.User.select()
        .join(Friends_list, on=Friends_list.friend)
        .where(Friends_list.user == current_user)
    )

    print(friends)  # Add this line to check the value of friends

    return render_template("my_friends.html", friends=friends)


@app.route("/unfriend/<username>", methods=["GET", "POST"])
@login_required
def unfriend(username):
    try:
        # Get the friend user object
        friend = models.User.get(User.username == username)

        # Delete the friendship records from Friends_list
        Friends_list.delete().where(
            ((Friends_list.user == current_user) & (Friends_list.friend == friend))
            | ((Friends_list.user == friend) & (Friends_list.friend == current_user))
        ).execute()

        # Delete the friendship records from Friendship
        Friendship.delete().where(
            ((Friendship.sender == current_user) & (Friendship.receiver == friend))
            | ((Friendship.sender == friend) & (Friendship.receiver == current_user))
        ).execute()

        flash("Unfriended successfully", "success")
    except User.DoesNotExist:
        flash("User not found", "error")

    return redirect(url_for("my_friends", username=username))


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


# if __name__ == "__main__":
#     models.initialize()
#     try:
#         models.User.create_user(
#             username="niteshsharma",
#             email="nbsharma@outlook.com",
#             password="password",
#             admin=True,
#         )
#     except ValueError:
#         pass
#     app.run(debug=DEBUG, host=HOST, port=PORT)
