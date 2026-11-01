
import json
import os
import re
from functools import wraps

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
USER_FILE = os.path.join(DATA_DIR, "users.json")


def load_users():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(USER_FILE):
        return {"users": []}

    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"users": []}


def save_users(data):
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({
                "success": False,
                "message": "请先登录"
            }), 401

        return func(*args, **kwargs)

    return wrapper


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "请填写完整信息"
        }), 400

    if len(username) > 30:
        return jsonify({
            "success": False,
            "message": "用户名不能超过30个字符"
        }), 400

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({
            "success": False,
            "message": "邮箱格式不正确"
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "密码至少需要6位"
        }), 400

    user_data = load_users()
    users = user_data["users"]

    for user in users:
        if user["email"] == email:
            return jsonify({
                "success": False,
                "message": "该邮箱已经注册"
            }), 409

    import uuid

    new_user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "email": email,
        "password": generate_password_hash(password)
    }

    users.append(new_user)
    save_users(user_data)

    session["user_id"] = new_user["id"]

    return jsonify({
        "success": True,
        "message": "注册成功",
        "user": {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"]
        }
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "请输入邮箱和密码"
        }), 400

    user_data = load_users()

    for user in user_data["users"]:
        if user["email"] == email:
            if check_password_hash(user["password"], password):
                session["user_id"] = user["id"]

                return jsonify({
                    "success": True,
                    "message": "登录成功",
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "email": user["email"]
                    }
                })

            break

    return jsonify({
        "success": False,
        "message": "邮箱或密码错误"
    }), 401


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    user_data = load_users()

    for user in user_data["users"]:
        if user["id"] == session["user_id"]:
            return jsonify({
                "success": True,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"]
                }
            })

    session.clear()

    return jsonify({
        "success": False,
        "message": "用户不存在"
    }), 404


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "已退出登录"
    })
