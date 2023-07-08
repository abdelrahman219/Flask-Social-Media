from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, HiddenField
from wtforms.validators import (
    DataRequired,
    Email,
    ValidationError,
    Length,
    EqualTo,
    Regexp,
)
from models import User, Friendship


def name_exists(form, field):
    if User.select().where(User.username == field.data).exists():
        raise ValidationError("User with this name already exists.")


def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError("User with this email already exists.")


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Regexp(
                r"^[a-zA-Z0-9_]+$",
                message="Username should be one word, letters, numbers, and underscores only.",
            ),
            name_exists,
        ],
        render_kw={"style": "width: 100%;"},
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), email_exists],
        render_kw={"style": "width: 100%;"},
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=2),
            EqualTo("password2", message="Passwords must match"),
        ],
        render_kw={"style": "width: 100%;"},
    )

    password2 = PasswordField(
        "Confirm Password",
        validators=[DataRequired()],
        render_kw={"style": "width: 100%;"},
    )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class PostForm(FlaskForm):
    content = TextAreaField(
        "Content", validators=[DataRequired()], render_kw={"style": "width: 100%;"}
    )
    privacy = SelectField(
        "Privacy",
        choices=[
            ("public", "Public"),
            ("friends_only", "Friends Only"),
            ("only_me", "Only Me"),
        ],
        default="public",
    )


class ProfileSettingsForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired()], render_kw={"style": "width: 100%;"}
    )
    email = StringField(
        "Email", validators=[DataRequired()], render_kw={"style": "width: 100%;"}
    )
    new_password = PasswordField("New Password", render_kw={"style": "width: 100%;"})
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[EqualTo("new_password", message="Passwords must match")],
        render_kw={"style": "width: 100%;"},
    )


class EditPostForm(FlaskForm):
    content = TextAreaField("Content", validators=[DataRequired()])
    privacy = SelectField(
        "Privacy",
        choices=[
            ("public", "Public"),
            ("friends_only", "Friends Only"),
            ("only_me", "only_me"),
        ],
        validators=[DataRequired()],
    )


class AddFriendForm(FlaskForm):
    # Hidden field to store receiver's user ID
    receiver_id = HiddenField("Receiver ID")
