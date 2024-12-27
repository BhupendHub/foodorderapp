from flask import Flask, render_template, redirect, url_for, session, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Order
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)
app.secret_key = "tecdev"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Sample Menu
'''
menu = [
    {"id": 1, "name": "Cheese Pizza", "price": 150, "image": "images/pizza.jpg"},
    {"id": 2, "name": "Veg Burger", "price": 110, "image": "images/burger.jpg"},
    {"id": 3, "name": "Briyani", "price": 130, "image": "images/briyani.jpg"},
    {"id": 4, "name": "Chole Kulche", "price": 120, "image": "images/kulche.jpg"},
]
'''
#Better option, read CSV using Pandas
df=pd.read_csv("dishes.csv")
menu=df.to_dict('records') #Convert DataFrame to List of Dictionary
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/menu")
def menu_page():
    return render_template("menu.html", menu=menu)

@app.route("/add_to_cart/<int:item_id>")
def add_to_cart(item_id):
    item = next((dish for dish in menu if dish["id"] == item_id), None)
    if item:
        cart = session.get("cart", [])
        cart.append(item)
        session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)
    return render_template("cart.html", cart=cart, total=total)

@app.route("/remove_from_cart/<int:item_id>")
def remove_from_cart(item_id):
    cart = session.get("cart", [])
    cart = [item for item in cart if item["id"] != item_id]
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["POST"])
def checkout():
    if "user_id" not in session:
        flash("Please log in to place an order.", "warning")
        return redirect(url_for("login"))

    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)
    new_order = Order(user_id=session["user_id"], items=str(cart), total=total)
    db.session.add(new_order)
    db.session.commit()

    session.pop("cart", None)
    return render_template("order_success.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        #hashed_password = generate_password_hash(password, method="sha256")
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login successful.", "success")
            return redirect(url_for("menu_page"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/order_history")
def order_history():
    if "user_id" not in session:
        flash("Please log in to view your order history.", "warning")
        return redirect(url_for("login"))

    orders = Order.query.filter_by(user_id=session["user_id"]).all()
    print('Orders are' ,type(orders))
    #for order in orders:
    #    print(order.items)
    return render_template("order_history.html", orders=orders)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

