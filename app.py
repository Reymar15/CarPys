from flask import Flask, render_template, request, redirect, url_for, session, make_response
from functools import wraps
from dotenv import load_dotenv
from flask_mail import Mail, Message
import os, httpx, hashlib, secrets, datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "drivelux_secret")

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
mail = Mail(app)

# In-memory token stores
reset_tokens = {}
login_codes = {}

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TIMEOUT = 15.0

def db(table):
    return f"{SUPABASE_URL}/rest/v1/{table}"

def headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def supabase_request(method, table, **kwargs):
    try:
        return httpx.request(method, db(table), headers=headers(), timeout=SUPABASE_TIMEOUT, **kwargs)
    except httpx.TimeoutException:
        return None
    except httpx.RequestError:
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response

ALL_BRAND_CARS = {
    "Range Rover": [
        {"id": "rr-sport", "name": "Range Rover Sport", "price": "₱95/day", "image": "https://images.unsplash.com/photo-1503376780353-7e6692767b70", "seats": 5, "transmission": "Automatic", "fuel": "Diesel", "category": "SUV"},
        {"id": "rr-vogue", "name": "Range Rover Vogue", "price": "₱150/day", "image": "https://images.unsplash.com/photo-1606016159991-dfe4f2746ad5", "seats": 5, "transmission": "Automatic", "fuel": "Diesel", "category": "SUV"},
        {"id": "rr-evoque", "name": "Range Rover Evoque", "price": "₱80/day", "image": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "SUV"},
        {"id": "rr-defender", "name": "Range Rover Defender", "price": "₱120/day", "image": "https://images.unsplash.com/photo-1609521263047-f8f205293f24", "seats": 5, "transmission": "Manual", "fuel": "Diesel", "category": "SUV"},
        {"id": "rr-discovery", "name": "Range Rover Discovery", "price": "₱100/day", "image": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b", "seats": 7, "transmission": "Automatic", "fuel": "Diesel", "category": "SUV"},
    ],
    "BMW": [
        {"id": "bmw-m4", "name": "BMW M4 Coupe", "price": "₱120/day", "image": "https://images.unsplash.com/photo-1511919884226-fd3cad34687c", "seats": 4, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "bmw-m3", "name": "BMW M3 Sedan", "price": "₱110/day", "image": "https://images.unsplash.com/photo-1555215695-3004980ad54e", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "bmw-x5", "name": "BMW X5 M", "price": "₱140/day", "image": "https://images.unsplash.com/photo-1556189250-72ba954cfc2b", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "SUV"},
        {"id": "bmw-m8", "name": "BMW M8 Gran Coupe", "price": "₱200/day", "image": "https://images.unsplash.com/photo-1556800572-1b8aeef2c54f", "seats": 4, "transmission": "Automatic", "fuel": "Petrol", "category": "Luxury"},
        {"id": "bmw-i8", "name": "BMW i8", "price": "₱250/day", "image": "https://images.unsplash.com/photo-1520031441872-265e4ff70366", "seats": 2, "transmission": "Automatic", "fuel": "Hybrid", "category": "Sports"},
    ],
    "Ferrari": [
        {"id": "ferrari-488", "name": "Ferrari 488", "price": "₱450/day", "image": "https://images.unsplash.com/photo-1502877338535-766e1452684a", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "ferrari-f8", "name": "Ferrari F8 Tributo", "price": "₱500/day", "image": "https://images.unsplash.com/photo-1583121274602-3e2820c69888", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "ferrari-roma", "name": "Ferrari Roma", "price": "₱420/day", "image": "https://images.unsplash.com/photo-1592198084033-aade902d1aae", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "ferrari-portofino", "name": "Ferrari Portofino", "price": "₱480/day", "image": "https://images.unsplash.com/photo-1544636331-e26879cd4d9b", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "ferrari-sf90", "name": "Ferrari SF90", "price": "₱800/day", "image": "https://images.unsplash.com/photo-1621135802920-133df287f89c", "seats": 2, "transmission": "Automatic", "fuel": "Hybrid", "category": "Sports"},
    ],
    "Mercedes": [
        {"id": "merc-sclass", "name": "Mercedes S-Class", "price": "₱200/day", "image": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "Luxury"},
        {"id": "merc-amg", "name": "Mercedes AMG GT", "price": "₱350/day", "image": "https://images.unsplash.com/photo-1553440569-bcc63803a83d", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "merc-gwagon", "name": "Mercedes G-Wagon", "price": "₱300/day", "image": "https://images.unsplash.com/photo-1520031441872-265e4ff70366", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "SUV"},
        {"id": "merc-eqs", "name": "Mercedes EQS", "price": "₱250/day", "image": "https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6", "seats": 5, "transmission": "Automatic", "fuel": "Electric", "category": "Luxury"},
        {"id": "merc-cls", "name": "Mercedes CLS", "price": "₱180/day", "image": "https://images.unsplash.com/photo-1563720223185-11003d516935", "seats": 4, "transmission": "Automatic", "fuel": "Petrol", "category": "Luxury"},
    ],
    "Lamborghini": [
        {"id": "lambo-urus", "name": "Lamborghini Urus", "price": "₱550/day", "image": "https://images.unsplash.com/photo-1544636331-e26879cd4d9b", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "SUV"},
        {"id": "lambo-huracan", "name": "Lamborghini Huracan", "price": "₱650/day", "image": "https://images.unsplash.com/photo-1519245659620-e859806a8d3b", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "lambo-aventador", "name": "Lamborghini Aventador", "price": "₱900/day", "image": "https://images.unsplash.com/photo-1525609004556-c46c7d6cf023", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "lambo-gallardo", "name": "Lamborghini Gallardo", "price": "₱500/day", "image": "https://images.unsplash.com/photo-1570733577524-3a047079e80d", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "lambo-sian", "name": "Lamborghini Sian", "price": "₱1200/day", "image": "https://images.unsplash.com/photo-1621135802920-133df287f89c", "seats": 2, "transmission": "Automatic", "fuel": "Hybrid", "category": "Sports"},
    ],
    "Porsche": [
        {"id": "porsche-911", "name": "Porsche 911", "price": "₱350/day", "image": "https://images.unsplash.com/photo-1503736334956-4c8f8e92946d", "seats": 4, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "porsche-cayenne", "name": "Porsche Cayenne", "price": "₱250/day", "image": "https://images.unsplash.com/photo-1580274455191-1c62238fa333", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "SUV"},
        {"id": "porsche-panamera", "name": "Porsche Panamera", "price": "₱280/day", "image": "https://images.unsplash.com/photo-1555652736-e92021d28a10", "seats": 4, "transmission": "Automatic", "fuel": "Petrol", "category": "Luxury"},
        {"id": "porsche-taycan", "name": "Porsche Taycan", "price": "₱320/day", "image": "https://images.unsplash.com/photo-1614162692292-7ac56d7f7f1e", "seats": 4, "transmission": "Automatic", "fuel": "Electric", "category": "Sports"},
        {"id": "porsche-macan", "name": "Porsche Macan", "price": "₱180/day", "image": "https://images.unsplash.com/photo-1611821064430-0d40291d0f0b", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "SUV"},
    ],
    "Audi": [
        {"id": "audi-r8", "name": "Audi R8", "price": "₱300/day", "image": "https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "audi-rs6", "name": "Audi RS6 Avant", "price": "₱220/day", "image": "https://images.unsplash.com/photo-1606152421802-db97b9c7a11b", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "audi-q8", "name": "Audi Q8", "price": "₱180/day", "image": "https://images.unsplash.com/photo-1614200179396-2bdb77ebf81b", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "SUV"},
        {"id": "audi-rs7", "name": "Audi RS7", "price": "₱260/day", "image": "https://images.unsplash.com/photo-1542362567-b07e54358753", "seats": 4, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "audi-etron", "name": "Audi e-tron GT", "price": "₱290/day", "image": "https://images.unsplash.com/photo-1617814076367-b759c7d7e738", "seats": 4, "transmission": "Automatic", "fuel": "Electric", "category": "Sports"},
    ],
    "Bentley": [
        {"id": "bentley-continental", "name": "Bentley Continental", "price": "₱600/day", "image": "https://images.unsplash.com/photo-1580274455191-1c62238fa333", "seats": 4, "transmission": "Automatic", "fuel": "Petrol", "category": "Luxury"},
        {"id": "bentley-flying-spur", "name": "Bentley Flying Spur", "price": "₱650/day", "image": "https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "Luxury"},
        {"id": "bentley-bentayga", "name": "Bentley Bentayga", "price": "₱700/day", "image": "https://images.unsplash.com/photo-1563720223185-11003d516935", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "SUV"},
        {"id": "bentley-mulsanne", "name": "Bentley Mulsanne", "price": "₱800/day", "image": "https://images.unsplash.com/photo-1631295868223-63265b40d9e4", "seats": 5, "transmission": "Automatic", "fuel": "Petrol", "category": "Luxury"},
        {"id": "bentley-gt-speed", "name": "Bentley GT Speed", "price": "₱750/day", "image": "https://images.unsplash.com/photo-1494976388531-d1058494cdd8", "seats": 4, "transmission": "Automatic", "fuel": "Petrol", "category": "Luxury"},
    ],
    "Toyota": [
        {"id": "toyota-landcruiser", "name": "Toyota Land Cruiser", "price": "₱150/day", "image": "https://images.unsplash.com/photo-1559416523-140ddc3d238c", "seats": 7, "transmission": "Automatic", "fuel": "Diesel", "category": "SUV"},
        {"id": "toyota-landcruiser-300", "name": "Toyota Land Cruiser 300", "price": "₱180/day", "image": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf", "seats": 7, "transmission": "Automatic", "fuel": "Diesel", "category": "SUV"},
        {"id": "toyota-prado", "name": "Toyota Land Cruiser Prado", "price": "₱130/day", "image": "https://images.unsplash.com/photo-1606016159991-dfe4f2746ad5", "seats": 7, "transmission": "Automatic", "fuel": "Diesel", "category": "SUV"},
        {"id": "toyota-fj", "name": "Toyota FJ Cruiser", "price": "₱110/day", "image": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b", "seats": 5, "transmission": "Manual", "fuel": "Petrol", "category": "SUV"},
        {"id": "toyota-fortuner", "name": "Toyota Fortuner", "price": "₱100/day", "image": "https://images.unsplash.com/photo-1609521263047-f8f205293f24", "seats": 7, "transmission": "Automatic", "fuel": "Diesel", "category": "SUV"},
    ],
    "McLaren": [
        {"id": "mclaren-720s", "name": "McLaren 720S", "price": "₱700/day", "image": "https://images.unsplash.com/photo-1621135802920-133df287f89c", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "mclaren-570s", "name": "McLaren 570S", "price": "₱550/day", "image": "https://images.unsplash.com/photo-1503376780353-7e6692767b70", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "mclaren-gt", "name": "McLaren GT", "price": "₱600/day", "image": "https://images.unsplash.com/photo-1544636331-e26879cd4d9b", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "mclaren-765lt", "name": "McLaren 765LT", "price": "₱850/day", "image": "https://images.unsplash.com/photo-1583121274602-3e2820c69888", "seats": 2, "transmission": "Automatic", "fuel": "Petrol", "category": "Sports"},
        {"id": "mclaren-artura", "name": "McLaren Artura", "price": "₱750/day", "image": "https://images.unsplash.com/photo-1525609004556-c46c7d6cf023", "seats": 2, "transmission": "Automatic", "fuel": "Hybrid", "category": "Sports"},
    ],
}

@app.route("/")
def home():
    cars = [
        {"name": "Range Rover", "price": "₱95/day", "image": "https://images.unsplash.com/photo-1503376780353-7e6692767b70"},
        {"name": "BMW", "price": "₱120/day", "image": "https://images.unsplash.com/photo-1511919884226-fd3cad34687c"},
        {"name": "Ferrari", "price": "₱450/day", "image": "https://images.unsplash.com/photo-1502877338535-766e1452684a"},
    ]
    return render_template("index.html", cars=cars, user=session.get("user"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    next_page = request.args.get("next") or "/"
    if request.method == "POST":
        identifier = request.form["email"]
        password = request.form["password"]
        next_page = request.form.get("next") or "/"
        hashed = hash_password(password)
        email_res = httpx.get(db("profiles"), headers=headers(), params={"email": f"eq.{identifier}", "password": f"eq.{hashed}"})
        username_res = httpx.get(db("profiles"), headers=headers(), params={"username": f"eq.{identifier}", "password": f"eq.{hashed}"})
        if email_res.status_code >= 400:
            error = f"Login failed: {email_res.text}"
            return render_template("login.html", error=error, next=next_page)
        if username_res.status_code >= 400:
            error = f"Login failed: {username_res.text}"
            return render_template("login.html", error=error, next=next_page)
        data = email_res.json() or username_res.json()
        if identifier == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            session["admin_user"] = ADMIN_USERNAME
            return redirect(url_for("admin_dashboard"))
        if data:
            if data[0].get("verified", False):
                session["admin"] = True
                session["admin_user"] = data[0]["username"]
                return redirect(url_for("admin_dashboard"))

            email = data[0]["email"]
            code = f"{secrets.randbelow(1000000):06d}"
            expires = (datetime.datetime.now() + datetime.timedelta(minutes=10)).isoformat()
            login_codes[email] = {
                "code": code,
                "username": data[0]["username"],
                "next": next_page,
                "expires": expires,
            }
            msg = Message("Your DriveLux login code", recipients=[email])
            msg.body = f"Your DriveLux login code is {code}. This code expires in 10 minutes."
            msg.html = f"""
            <h2>Your DriveLux login code</h2>
            <p>Use this code to finish signing in:</p>
            <h1 style="letter-spacing:4px;">{code}</h1>
            <p>This code expires in 10 minutes.</p>
            """
            mail.send(msg)
            session["pending_login_email"] = email
            return redirect(url_for("login_code"))
        else:
            error = "Invalid email or password."
    return render_template("login.html", error=error, next=next_page)

@app.route("/login-code", methods=["GET", "POST"])
def login_code():
    email = session.get("pending_login_email")
    if not email:
        return redirect(url_for("login"))

    error = None
    if request.method == "POST":
        code = request.form["code"].strip()
        data = login_codes.get(email)
        if not data:
            error = "Login code expired. Please sign in again."
        elif datetime.datetime.now().isoformat() > data["expires"]:
            login_codes.pop(email, None)
            session.pop("pending_login_email", None)
            error = "Login code expired. Please sign in again."
        elif code != data["code"]:
            error = "Invalid code."
        else:
            session["user"] = data["username"]
            session["email"] = email
            next_page = data["next"]
            login_codes.pop(email, None)
            session.pop("pending_login_email", None)
            return redirect(next_page)

    return render_template("login_code.html", error=error, email=email)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed = hash_password(password)
        check = httpx.get(db("profiles"), headers=headers(), params={"email": f"eq.{email}"})
        if check.status_code >= 400:
            error = f"Could not check account: {check.text}"
            return render_template("signup.html", error=error)
        existing_profiles = check.json()
        if existing_profiles:
            existing = existing_profiles[0]
            error = "Email already registered."
        else:
            create_res = httpx.post(db("profiles"), headers=headers(), json={"username": username, "email": email, "password": hashed, "verified": False})
            if create_res.status_code >= 400:
                error = f"Could not create account: {create_res.text}"
                return render_template("signup.html", error=error)
            return redirect(url_for("login"))
    return render_template("signup.html", error=error)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None
    if request.method == "POST":
        email = request.form["email"]
        check = httpx.get(db("profiles"), headers=headers(), params={"email": f"eq.{email}"})
        if check.json():
            token = secrets.token_urlsafe(32)
            expires = (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()
            reset_tokens[token] = {"email": email, "expires": expires}
            reset_url = url_for("reset_password", token=token, _external=True)
            msg = Message("Reset your DriveLux password", recipients=[email])
            msg.html = f"""
            <h2>Password Reset Request</h2>
            <p>Click the button below to reset your password:</p>
            <a href="{reset_url}" style="background:#FFD700;padding:12px 24px;text-decoration:none;font-weight:bold;border-radius:4px;">Reset Password</a>
            <p>This link expires in 1 hour. If you did not request this, ignore this email.</p>
            """
            mail.send(msg)
        message = "If that email exists, a reset link has been sent."
    return render_template("forgot_password.html", message=message)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    data = reset_tokens.get(token)
    if not data or datetime.datetime.now().isoformat() > data["expires"]:
        return render_template("verify_result.html", success=False, message="Invalid or expired reset link.")
    error = None
    if request.method == "POST":
        password = request.form["password"]
        hashed = hash_password(password)
        httpx.patch(db("profiles"), headers=headers(), params={"email": f"eq.{data['email']}"}, json={"password": hashed})
        reset_tokens.pop(token, None)
        return render_template("verify_result.html", success=True, message="Password reset successful! You can now login.")
    return render_template("reset_password.html", token=token, error=error)

@app.route("/cars")
def cars():
    all_cars = [
        {"id": 1, "name": "Range Rover", "price": "₱95/day", "image": "https://images.unsplash.com/photo-1503376780353-7e6692767b70", "category": "SUV"},
        {"id": 2, "name": "BMW", "price": "₱120/day", "image": "https://images.unsplash.com/photo-1511919884226-fd3cad34687c", "category": "Sports"},
        {"id": 3, "name": "Ferrari", "price": "₱450/day", "image": "https://images.unsplash.com/photo-1502877338535-766e1452684a", "category": "Sports"},
        {"id": 4, "name": "Mercedes", "price": "₱200/day", "image": "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8", "category": "Luxury"},
        {"id": 5, "name": "Lamborghini", "price": "₱550/day", "image": "https://images.unsplash.com/photo-1544636331-e26879cd4d9b", "category": "SUV"},
        {"id": 6, "name": "Porsche", "price": "₱350/day", "image": "https://images.unsplash.com/photo-1503736334956-4c8f8e92946d", "category": "Sports"},
        {"id": 7, "name": "Audi", "price": "₱300/day", "image": "https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a", "category": "Sports"},
        {"id": 8, "name": "Bentley Continental", "price": "₱600/day", "image": "https://images.unsplash.com/photo-1580274455191-1c62238fa333", "category": "Luxury"},
        {"id": 9, "name": "Toyota Land Cruiser", "price": "₱150/day", "image": "https://images.unsplash.com/photo-1559416523-140ddc3d238c", "category": "SUV"},
        {"id": 10, "name": "McLaren", "price": "₱700/day", "image": "https://images.unsplash.com/photo-1621135802920-133df287f89c", "category": "Sports"},
    ]
    return render_template("cars.html", cars=all_cars, user=session.get("user"))

@app.route("/brand/<brand_name>")
def brand(brand_name):
    selected = ALL_BRAND_CARS.get(brand_name, [])
    return render_template("brand.html", brand_name=brand_name, cars=selected, user=session.get("user"))

@app.route("/car/<car_id>")
def car_detail(car_id):
    car = None
    for brand_cars in ALL_BRAND_CARS.values():
        for c in brand_cars:
            if c["id"] == car_id:
                car = c
                break
    if not car:
        return redirect(url_for("cars"))
    return render_template("car_detail.html", car=car, user=session.get("user"))

@app.route("/book/<car_id>", methods=["GET", "POST"])
def book(car_id):
    if not session.get("user"):
        return redirect(url_for("login", next=url_for("book", car_id=car_id)))
    car = None
    for brand_cars in ALL_BRAND_CARS.values():
        for c in brand_cars:
            if c["id"] == car_id:
                car = c
                break
    if not car:
        return redirect(url_for("cars"))
    if request.method == "POST":
        pickup = request.form["pickup"]
        dropoff = request.form["dropoff"]
        httpx.post(db("bookings"), headers=headers(), json={
            "user_email": session.get("email"),
            "username": session["user"],
            "car_id": car["id"],
            "car_name": car["name"],
            "car_image": car["image"],
            "car_price": car["price"],
            "pickup_date": pickup,
            "dropoff_date": dropoff,
            "status": "Pending Pickup"
        })
        return redirect(url_for("my_bookings"))
    return render_template("book.html", car=car, user=session.get("user"))

@app.route("/bookings")
def my_bookings():
    if not session.get("user"):
        return redirect(url_for("login", next=url_for("my_bookings")))
    res = supabase_request("GET", "bookings", params={"username": f"eq.{session['user']}", "order": "created_at.desc"})
    if res is None:
        return render_template("bookings.html", bookings=[], user=session.get("user"), error="Could not connect to Supabase. Please try again.")
    if res.status_code >= 400:
        return render_template("bookings.html", bookings=[], user=session.get("user"), error=f"Could not load bookings: {res.text}")
    user_bookings = [{"id": b["id"], "car": {"name": b["car_name"], "image": b["car_image"], "price": b["car_price"]}, "pickup": b["pickup_date"], "dropoff": b["dropoff_date"], "status": b["status"]} for b in res.json()]
    return render_template("bookings.html", bookings=user_bookings, user=session.get("user"))

@app.route("/bookings/<booking_id>/confirm-pickup", methods=["POST"])
def confirm_pickup(booking_id):
    if not session.get("user"):
        return redirect(url_for("login", next=url_for("my_bookings")))
    booking_res = supabase_request(
        "GET",
        "bookings",
        params={"id": f"eq.{booking_id}", "username": f"eq.{session['user']}"},
    )
    booking_data = booking_res.json() if booking_res is not None and booking_res.status_code < 400 else []
    update_res = supabase_request(
        "PATCH",
        "bookings",
        params={"id": f"eq.{booking_id}", "username": f"eq.{session['user']}"},
        json={"status": "Pickup Confirmed"}
    )
    if update_res is not None and update_res.status_code < 400 and booking_data:
        booking = booking_data[0]
        admin_email = os.getenv("ADMIN_EMAIL") or app.config["MAIL_DEFAULT_SENDER"] or app.config["MAIL_USERNAME"]
        msg = Message("DriveLux pick-up confirmed", recipients=[admin_email])
        msg.body = (
            f"{booking['username']} confirmed car pick-up.\n\n"
            f"Car: {booking['car_name']}\n"
            f"Pick-up date: {booking['pickup_date']}\n"
            f"Drop-off date: {booking['dropoff_date']}\n"
            f"Price: {booking['car_price']}\n"
            f"User email: {booking.get('user_email') or 'N/A'}"
        )
        msg.html = f"""
        <h2>DriveLux pick-up confirmed</h2>
        <p><strong>{booking['username']}</strong> confirmed car pick-up.</p>
        <ul>
          <li><strong>Car:</strong> {booking['car_name']}</li>
          <li><strong>Pick-up date:</strong> {booking['pickup_date']}</li>
          <li><strong>Drop-off date:</strong> {booking['dropoff_date']}</li>
          <li><strong>Price:</strong> {booking['car_price']}</li>
          <li><strong>User email:</strong> {booking.get('user_email') or 'N/A'}</li>
        </ul>
        """
        mail.send(msg)
    return redirect(url_for("my_bookings"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("email", None)
    return redirect(url_for("home"))

# ADMIN
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    return redirect(url_for("login"))

@app.route("/admin/create-account", methods=["GET", "POST"])
@admin_required
def admin_create_account():
    error = None
    message = None
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        hashed = hash_password(password)
        check = httpx.get(db("profiles"), headers=headers(), params={"email": f"eq.{email}"})
        if check.status_code >= 400:
            error = f"Could not check account: {check.text}"
            return render_template("admin/create_account.html", error=error, message=message)
        if check.json():
            error = "Email already registered."
        else:
            create_res = httpx.post(db("profiles"), headers=headers(), json={"username": username, "email": email, "password": hashed, "verified": True})
            if create_res.status_code >= 400:
                error = f"Could not create admin account: {create_res.text}"
            else:
                message = "Admin account created."
    return render_template("admin/create_account.html", error=error, message=message)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    session.pop("admin_user", None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    total_cars = sum(len(v) for v in ALL_BRAND_CARS.values())
    total_users = len(httpx.get(db("profiles"), headers=headers(), params={"select": "id"}).json())
    total_bookings = len(httpx.get(db("bookings"), headers=headers(), params={"select": "id"}).json())
    return render_template("admin/dashboard.html", total_cars=total_cars, total_users=total_users, total_bookings=total_bookings)

@app.route("/admin/cars")
@admin_required
def admin_cars():
    all_cars = [(brand, car) for brand, cars in ALL_BRAND_CARS.items() for car in cars]
    return render_template("admin/cars.html", all_cars=all_cars)

@app.route("/admin/cars/delete/<car_id>")
@admin_required
def admin_delete_car(car_id):
    for brand in ALL_BRAND_CARS:
        ALL_BRAND_CARS[brand] = [c for c in ALL_BRAND_CARS[brand] if c["id"] != car_id]
    return redirect(url_for("admin_cars"))

@app.route("/admin/users")
@admin_required
def admin_users():
    users_data = httpx.get(db("profiles"), headers=headers(), params={"select": "username,email,created_at", "order": "created_at.desc"}).json()
    return render_template("admin/users.html", users=users_data)

@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    data = httpx.get(db("bookings"), headers=headers(), params={"order": "created_at.desc"}).json()
    all_bookings = [(b["username"], {"id": b["id"], "car": {"name": b["car_name"], "image": b["car_image"], "price": b["car_price"]}, "pickup": b["pickup_date"], "dropoff": b["dropoff_date"], "status": b["status"]}) for b in data]
    return render_template("admin/bookings.html", all_bookings=all_bookings)

@app.route("/admin/bookings/<booking_id>/confirm-dropoff", methods=["POST"])
@admin_required
def admin_confirm_dropoff(booking_id):
    httpx.patch(
        db("bookings"),
        headers=headers(),
        params={"id": f"eq.{booking_id}"},
        json={"status": "Drop-off Confirmed"}
    )
    return redirect(url_for("admin_bookings"))

if __name__ == "__main__":
    app.run(debug=True)
