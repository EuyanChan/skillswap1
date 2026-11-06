
from flask import Flask, render_template
import os

from backend.auth import auth_bp
from backend.skills import skills_bp
from backend.matching import matching_bp
from backend.exchanges import exchanges_bp


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)

# Session 密钥：本地开发临时使用
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "local-development-key-change-before-deployment"
)

# 注册用户认证蓝图
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(skills_bp, url_prefix="/api/skills")
app.register_blueprint(
    matching_bp,
    url_prefix="/api/matching"
)
app.register_blueprint(
    exchanges_bp,
    url_prefix="/api/exchanges"
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return {
        "status": "success",
        "message": "SkillSwap is running!"
    }


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
