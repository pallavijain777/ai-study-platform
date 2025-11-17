import random, string, jwt
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message
from agent_learn_api import db, bcrypt, mail
from agent_learn_api.models.user import User
from agent_learn_api.models.verification_codes import VerificationCode

auth_bp = Blueprint("auth", __name__)

pending_requests = {}

# --- Signup route ---
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username, email, password, dob_str = (
        data.get("username"),
        data.get("email"),
        data.get("password"),
        data.get("dob"),
    )

    if not username or not email or not password or not dob_str:
        return jsonify({"error": "All fields are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

    # Generate verification code
    code = "".join(random.choices(string.ascii_letters + string.digits, k=6))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    # Save verification code in DB
    verification = VerificationCode(email=email, code=code, expires_at=expires_at)
    db.session.add(verification)
    db.session.commit()

    # Store signup info temporarily
    pending_requests[email] = {"username": username, "password": hashed_pw, "dob": dob}

    # Send email
    try:
        msg = Message(
            "Verify your Signup",
            sender=current_app.config["MAIL_USERNAME"],
            recipients=[email],
        )
        msg.body = f"Your verification code is: {code}"
        print(msg.body)  # Debug log
        mail.send(msg)
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

    return jsonify({"message": "Verification code sent to email"}), 200


# --- Verify route ---
@auth_bp.route("/verify", methods=["POST"])
def verify():
    data = request.json
    email, code = data.get("email"), data.get("code")

    if not email or not code:
        return jsonify({"error": "Email and code are required"}), 400

    if email not in pending_requests:
        return jsonify({"error": "No signup request found for this email"}), 400

    record = VerificationCode.query.filter_by(email=email, code=code).first()
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # make naive
    if not record or record.expires_at < now:
        return jsonify({"error": "Invalid or expired verification code"}), 400

    # Insert new user into DB
    signup_info = pending_requests[email]
    print(signup_info)
    new_user = User(
        username=signup_info["username"],
        email=email,
        password=signup_info["password"],
        dob=signup_info["dob"],
        is_verified=True,
    )
    db.session.add(new_user)

    # Cleanup
    db.session.delete(record)
    db.session.commit()
    del pending_requests[email]

    return jsonify({"message": "User verified and registered successfully"}), 201


# --- Login route ---
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email, password_entered = data.get("email"), data.get("password")

    if not email or not password_entered:
        return jsonify({"error": "All fields are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not bcrypt.check_password_hash(user.password, password_entered):
        return jsonify({"error": "Wrong password"}), 400

    # Generate token
    expiration = datetime.now(timezone.utc) + timedelta(days=5)
    token = jwt.encode(
        {"user_id": user.id, "exp": expiration},
        current_app.config.get("SECRET_KEY", "dev_secret"),
        algorithm="HS256",
    )

    return jsonify({
        "token": token,
        "id": user.id,
        "username": user.username,
        "age": user.age,
    }), 200


# --- ID Login route ---
@auth_bp.route("/idlogin", methods=["POST"])
def idlogin():
    data = request.json
    token = data.get("token")
    if not token:
        return jsonify({"error": "All fields are required"}), 400

    try:
        # Verify token
        payload = jwt.decode(
            token,
            current_app.config.get("SECRET_KEY", "dev_secret"),
            algorithms=["HS256"],
        )
        user_id = payload["user_id"]
        user = User.query.get(user_id)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "age": user.age,
    }), 200
