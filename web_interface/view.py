from flask import Blueprint, render_template, url_for, redirect
from flask_login import login_required, current_user

view = Blueprint('view', __name__)


@view.route("/")
@view.route("/home")
def home():
    # if current_user.is_authenticated:
    #     return redirect(url_for("view.dashboard"))

    return render_template("home.html", user=current_user)


@view.route("/dashboard")
@login_required
def dashboard():
    return render_template("control.html", active_page="dashboard",user=current_user)

@view.route("/about")
def about():
    return render_template('about.html')

@view.route("/pdf")
@login_required
def pdf_page():
    return render_template("pdf.html", active_page="pdf",user=current_user)

@view.route("/Games")
def Games():
    return render_template("Games.html", active_page="Games",user=current_user)

@view.route("/settings")
@login_required
def settings():
    return render_template("settings.html", active_page="settings",user=current_user)
@view.route("/programming")
@login_required
def programming():
    return render_template("programming.html", active_page="programming",user=current_user)

@view.route("/account")
@login_required
def account():
    return render_template("account.html", active_page="account",user=current_user)