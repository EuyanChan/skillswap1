
import json
import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, session

from backend.auth import login_required, load_users

skills_bp = Blueprint("skills", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SKILL_FILE = os.path.join(DATA_DIR, "skills.json")


# 技能分类及对应图标
ICON_MAP = {
    "编程技术": "💻",
    "语言学习": "🌍",
    "艺术设计": "🎨",
    "生活兴趣": "✨"
}

ALLOWED_CATEGORIES = list(ICON_MAP.keys())


# 读取技能数据
def load_skills():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(SKILL_FILE):
        return {"skills": []}

    try:
        with open(SKILL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"skills": []}


# 保存技能数据
def save_skills(data):
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(SKILL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# 获取技能列表
@skills_bp.route("/", methods=["GET"])
def get_skills():
    skill_data = load_skills()
    user_data = load_users()

    # 根据 user_id 找到发布者用户名
    user_map = {
        user["id"]: user["username"]
        for user in user_data["users"]
    }

    result = []

    for skill in reversed(skill_data["skills"]):
        result.append({
            "id": skill["id"],
            "name": skill["name"],
            "category": skill["category"],
            "icon": skill["icon"],
            "description": skill["description"],
            "person": user_map.get(skill["user_id"], "未知用户"),
            "is_mine": skill["user_id"] == session.get("user_id"),
            "location": skill.get("location", "未填写"),
            "wanted": skill["wanted"]
        })

    return jsonify({
        "success": True,
        "skills": result
    })


# 发布技能
@skills_bp.route("/", methods=["POST"])
@login_required
def publish_skill():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    wanted = data.get("wanted", "").strip()

    if not name or not category or not description:
        return jsonify({
            "success": False,
            "message": "请填写完整的技能信息"
        }), 400

    if len(name) > 50:
        return jsonify({
            "success": False,
            "message": "技能名称不能超过50个字符"
        }), 400

    if category not in ALLOWED_CATEGORIES:
        return jsonify({
            "success": False,
            "message": "技能分类不正确"
        }), 400

    if len(description) > 500:
        return jsonify({
            "success": False,
            "message": "技能介绍不能超过500个字符"
        }), 400

    if len(wanted) > 100:
        return jsonify({
            "success": False,
            "message": "希望交换的技能不能超过100个字符"
        }), 400

    skill_data = load_skills()

    new_skill = {
        "id": str(uuid.uuid4()),
        "user_id": session["user_id"],
        "name": name,
        "category": category,
        "icon": ICON_MAP[category],
        "description": description,
        "wanted": wanted or "暂无指定",
        "location": "未填写",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    skill_data["skills"].append(new_skill)
    save_skills(skill_data)

    user_data = load_users()
    username = next(
        (
            user["username"]
            for user in user_data["users"]
            if user["id"] == session["user_id"]
        ),
        "未知用户"
    )

    return jsonify({
        "success": True,
        "message": "技能发布成功！",
        "skill": {
            "id": new_skill["id"],
            "name": new_skill["name"],
            "category": new_skill["category"],
            "icon": new_skill["icon"],
            "description": new_skill["description"],
            "person": username,
            "location": new_skill["location"],
            "wanted": new_skill["wanted"]
        }
    }), 201


@skills_bp.route("/<skill_id>", methods=["PUT"])
@login_required
def update_skill(skill_id):
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    wanted = data.get("wanted", "").strip()

    if not name or not category or not description:
        return jsonify({
            "success": False,
            "message": "技能名称、分类和描述不能为空"
        }), 400

    if category not in ALLOWED_CATEGORIES:
        return jsonify({
            "success": False,
            "message": "技能分类不正确"
        }), 400

    if len(name) > 50 or len(description) > 500 or len(wanted) > 100:
        return jsonify({
            "success": False,
            "message": "输入内容过长"
        }), 400

    skill_data = load_skills()

    skill = next(
        (item for item in skill_data["skills"]
         if item["id"] == skill_id),
        None
    )

    if skill is None:
        return jsonify({
            "success": False,
            "message": "技能不存在"
        }), 404

    # 只能编辑自己发布的技能
    if skill["user_id"] != session["user_id"]:
        return jsonify({
            "success": False,
            "message": "无权编辑该技能"
        }), 403

    skill["name"] = name
    skill["category"] = category
    skill["icon"] = ICON_MAP[category]
    skill["description"] = description
    skill["wanted"] = wanted or "暂无指定"

    save_skills(skill_data)

    return jsonify({
        "success": True,
        "message": "技能修改成功！"
    })


@skills_bp.route("/<skill_id>", methods=["DELETE"])
@login_required
def delete_skill(skill_id):
    skill_data = load_skills()

    skill = next(
        (item for item in skill_data["skills"]
         if item["id"] == skill_id),
        None
    )

    if skill is None:
        return jsonify({
            "success": False,
            "message": "技能不存在"
        }), 404

    # 只能删除自己发布的技能
    if skill["user_id"] != session["user_id"]:
        return jsonify({
            "success": False,
            "message": "无权删除该技能"
        }), 403

    skill_data["skills"] = [
        item for item in skill_data["skills"]
        if item["id"] != skill_id
    ]

    save_skills(skill_data)

    return jsonify({
        "success": True,
        "message": "技能删除成功！"
    })
