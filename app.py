from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>技能互换平台</title>
        <style>
            body { font-family: sans-serif; text-align: center; margin-top: 100px; background-color: #f4f4f9; }
            h1 { color: #333; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <h1>🎉 技能互换平台已成功部署！</h1>
        <p>这是一个基于 Flask 的雏形链接，域名已固定，随时可以持续迭代。</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True)
