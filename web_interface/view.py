from flask import Blueprint, render_template
from flask_login import login_required, current_user

view = Blueprint('view', __name__)


@view.route("/home")
@login_required
def home():
    return render_template('home.html',user=current_user)

@view.route("/about")
def about():
    return render_template('about.html')

@view.route("/")
@view.route("/dashboard")
@login_required
def dashboard():
    return render_template("control.html", active_page="dashboard",user=current_user)

@view.route("/pdf")
@login_required
def pdf_page():
    return render_template("pdf.html", active_page="pdf",user=current_user)

@view.route("/teachback")
def teachback():
    return render_template("teachback.html", active_page="teachback",user=current_user)

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