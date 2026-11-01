from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# --- 模拟数据库 (内存版) ---
# 当前登录用户 (固定为 1)
current_user_id = 1

# 用户表
users = {
    1: {"id": 1, "name": "尤安 (我)", "city": "北京", "teach": "Python", "learn": "吉他", "avatar": "👨‍💻"},
    2: {"id": 2, "name": "小林", "city": "北京", "teach": "吉他", "learn": "Python", "avatar": "👩‍🎸"},
    3: {"id": 3, "name": "老王", "city": "上海", "teach": "摄影", "learn": "英语", "avatar": "👨‍📷"},
    4: {"id": 4, "name": "Alice", "city": "北京", "teach": "英语", "learn": "摄影", "avatar": "👩‍🎓"}
}

# 互换契约表
contracts = [
    # 示例：初始化一个进行中的契约
    {"id": 1, "user_a": 1, "user_b": 3, "skill_a": "Python", "skill_b": "摄影", "status": "进行中"}
]

# --- 路由 ---

@app.route('/')
def index():
    # 匹配逻辑：寻找 对方想学的 == 我想教的，且 对方能教的 == 我想学的
    me = users[current_user_id]
    matches = []
    for u in users.values():
        if u['id'] == me['id']: continue
        # 双向匹配判定
        if u['learn'] == me['teach'] and u['teach'] == me['learn']:
            u['match_reason'] = f"TA想学 {u['learn']}，正好你会；TA会 {u['teach']}，正好你想学！"
            matches.append(u)
        # 单向匹配（降级展示）
        elif u['learn'] == me['teach'] or u['teach'] == me['learn']:
            u['match_reason'] = f"存在互补技能：{u['teach']} ↔ {u['learn']}"
            matches.append(u)
            
    return render_template('index.html', me=me, matches=matches)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    me = users[current_user_id]
    if request.method == 'POST':
        # 更新技能
        me['teach'] = request.form.get('teach')
        me['learn'] = request.form.get('learn')
        return redirect(url_for('index'))
    return render_template('profile.html', me=me)

@app.route('/swap/<int:target_id>')
def make_swap(target_id):
    # 发起互换
    me = users[current_user_id]
    target = users.get(target_id)
    if target:
        new_contract = {
            "id": len(contracts) + 1,
            "user_a": me['id'],
            "user_b": target['id'],
            "skill_a": me['teach'],
            "skill_b": target['teach'],
            "status": "等待对方确认"
        }
        contracts.append(new_contract)
    return redirect(url_for('swaps'))

@app.route('/swaps')
def swaps():
    me = users[current_user_id]
    my_contracts = [c for c in contracts if c['user_a'] == me['id'] or c['user_b'] == me['id']]
    # 补充对方的名字方便展示
    for c in my_contracts:
        other_id = c['user_b'] if c['user_a'] == me['id'] else c['user_a']
        c['other_name'] = users[other_id]['name']
    return render_template('swaps.html', me=me, contracts=my_contracts)

if __name__ == '__main__':
    app.run(debug=True)