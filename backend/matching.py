
import json
import os

from flask import Blueprint, jsonify, session

from backend.auth import login_required, load_users
from backend.skills import load_skills


matching_bp = Blueprint("matching", __name__)


def normalize_skill(skill_name):
    """
    统一技能名称格式：
    去除首尾空格，并忽略大小写。
    """
    return skill_name.strip().lower()


def find_matches():
    """
    查找当前用户与其他用户之间的技能匹配。
    """

    current_user_id = session.get("user_id")

    skill_data = load_skills()
    user_data = load_users()

    all_skills = skill_data["skills"]
    all_users = user_data["users"]

    # 获取当前用户发布的技能
    my_skills = [
        skill for skill in all_skills
        if skill["user_id"] == current_user_id
    ]

    # 用户ID对应用户名
    user_map = {
        user["id"]: user["username"]
        for user in all_users
    }

    matches = []

    # 遍历其他用户的技能
    for other_skill in all_skills:

        # 排除自己的技能
        if other_skill["user_id"] == current_user_id:
            continue

        other_user_id = other_skill["user_id"]

        # 防止同一个用户重复匹配
        if any(
            match["user_id"] == other_user_id
            for match in matches
        ):
            continue

        # 当前用户与对方是否双向匹配
        for my_skill in my_skills:

            my_teach = normalize_skill(
                my_skill["name"]
            )

            my_want = normalize_skill(
                my_skill["wanted"]
            )

            other_teach = normalize_skill(
                other_skill["name"]
            )

            other_want = normalize_skill(
                other_skill["wanted"]
            )

            # A能教的技能，是B想学的
            first_match = (
                my_teach == other_want
            )

            # B能教的技能，是A想学的
            second_match = (
                other_teach == my_want
            )

            # 双向匹配
            if first_match and second_match:

                matches.append({
                    "user_id": other_user_id,
                    "username": user_map.get(
                        other_user_id,
                        "未知用户"
                    ),
                    "match_type": "双向匹配",
                    "my_skill": my_skill["name"],
                    "their_skill": other_skill["name"]
                })

                break

    return matches


@matching_bp.route("/", methods=["GET"])
@login_required
def get_matches():

    matches = find_matches()

    return jsonify({
        "success": True,
        "matches": matches
    })
