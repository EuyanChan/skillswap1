
from flask import Blueprint, request, jsonify, session

from backend.auth import login_required, load_users
from backend.skills import load_skills

import json
import os
import uuid
from datetime import datetime, timezone


exchanges_bp = Blueprint("exchanges", __name__)


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.path.join(BASE_DIR, "data")

EXCHANGE_FILE = os.path.join(
    DATA_DIR,
    "exchanges.json"
)


def load_exchanges():
    """
    读取交换申请数据
    """

    if not os.path.exists(EXCHANGE_FILE):
        return {"exchanges": []}

    with open(EXCHANGE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_exchanges(data):
    """
    保存交换申请数据
    """

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(EXCHANGE_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


def get_username(user_id):
    """
    根据用户ID获取用户名
    """

    user_data = load_users()

    for user in user_data["users"]:
        if user["id"] == user_id:
            return user["username"]

    return "未知用户"


def get_skill_by_name(user_id, skill_name):
    """
    根据用户ID和技能名称查找技能
    """

    skill_data = load_skills()

    for skill in skill_data["skills"]:
        if (
            skill["user_id"] == user_id
            and skill["name"].strip().lower()
            == skill_name.strip().lower()
        ):
            return skill

    return None


@exchanges_bp.route("/", methods=["GET"])
@login_required
def get_exchanges():
    """
    获取当前用户发出的申请和收到的申请
    """

    current_user_id = session["user_id"]

    exchange_data = load_exchanges()

    result = []

    for exchange in exchange_data["exchanges"]:

        # 只展示与当前用户有关的申请
        if (
            exchange["sender_id"] != current_user_id
            and exchange["receiver_id"] != current_user_id
        ):
            continue

        item = exchange.copy()

        item["sender_username"] = get_username(
            exchange["sender_id"]
        )

        item["receiver_username"] = get_username(
            exchange["receiver_id"]
        )

        item["is_sender"] = (
            exchange["sender_id"] == current_user_id
        )

        result.append(item)

    return jsonify({
        "success": True,
        "exchanges": result
    })


@exchanges_bp.route("/", methods=["POST"])
@login_required
def create_exchange():
    """
    创建交换申请
    """

    data = request.get_json(silent=True) or {}

    receiver_id = data.get("receiver_id", "").strip()
    my_skill_name = data.get("my_skill", "").strip()
    their_skill_name = data.get("their_skill", "").strip()

    sender_id = session["user_id"]

    # 必填检查
    if not receiver_id or not my_skill_name or not their_skill_name:
        return jsonify({
            "success": False,
            "message": "交换信息不完整"
        }), 400

    # 不允许自己向自己申请
    if sender_id == receiver_id:
        return jsonify({
            "success": False,
            "message": "不能向自己申请交换"
        }), 400

    # 检查接收用户是否存在
    user_data = load_users()

    receiver_exists = any(
        user["id"] == receiver_id
        for user in user_data["users"]
    )

    if not receiver_exists:
        return jsonify({
            "success": False,
            "message": "申请对象不存在"
        }), 404

    # 检查双方技能是否存在且归属正确
    my_skill = get_skill_by_name(
        sender_id,
        my_skill_name
    )

    their_skill = get_skill_by_name(
        receiver_id,
        their_skill_name
    )

    if my_skill is None or their_skill is None:
        return jsonify({
            "success": False,
            "message": "技能不存在或不属于对应用户"
        }), 400

    exchange_data = load_exchanges()

    # 防止重复申请
    for exchange in exchange_data["exchanges"]:

        same_pair = (
            exchange["sender_id"] == sender_id
            and exchange["receiver_id"] == receiver_id
            and exchange["my_skill"] == my_skill_name
            and exchange["their_skill"] == their_skill_name
        )

        if same_pair and exchange["status"] in [
            "待处理",
            "进行中"
        ]:
            return jsonify({
                "success": False,
                "message": "该交换申请已经存在"
            }), 400

    new_exchange = {
        "id": str(uuid.uuid4()),
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "my_skill": my_skill_name,
        "their_skill": their_skill_name,
        "status": "待处理",
        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    exchange_data["exchanges"].append(
        new_exchange
    )

    save_exchanges(exchange_data)

    return jsonify({
        "success": True,
        "message": "交换申请发送成功！",
        "exchange": new_exchange
    }), 201


@exchanges_bp.route("/<exchange_id>/accept", methods=["POST"])
@login_required
def accept_exchange(exchange_id):
    """
    接受交换申请
    """

    current_user_id = session["user_id"]

    exchange_data = load_exchanges()

    exchange = next(
        (
            item for item in exchange_data["exchanges"]
            if item["id"] == exchange_id
        ),
        None
    )

    if exchange is None:
        return jsonify({
            "success": False,
            "message": "交换申请不存在"
        }), 404

    # 只有接收方可以接受
    if exchange["receiver_id"] != current_user_id:
        return jsonify({
            "success": False,
            "message": "无权处理该申请"
        }), 403

    if exchange["status"] != "待处理":
        return jsonify({
            "success": False,
            "message": "该申请已经处理"
        }), 400

    exchange["status"] = "进行中"

    save_exchanges(exchange_data)

    return jsonify({
        "success": True,
        "message": "已接受交换申请！"
    })


@exchanges_bp.route("/<exchange_id>/reject", methods=["POST"])
@login_required
def reject_exchange(exchange_id):
    """
    拒绝交换申请
    """

    current_user_id = session["user_id"]

    exchange_data = load_exchanges()

    exchange = next(
        (
            item for item in exchange_data["exchanges"]
            if item["id"] == exchange_id
        ),
        None
    )

    if exchange is None:
        return jsonify({
            "success": False,
            "message": "交换申请不存在"
        }), 404

    # 只有接收方可以拒绝
    if exchange["receiver_id"] != current_user_id:
        return jsonify({
            "success": False,
            "message": "无权处理该申请"
        }), 403

    if exchange["status"] != "待处理":
        return jsonify({
            "success": False,
            "message": "该申请已经处理"
        }), 400

    exchange["status"] = "已拒绝"

    save_exchanges(exchange_data)

    return jsonify({
        "success": True,
        "message": "已拒绝交换申请"
    })
