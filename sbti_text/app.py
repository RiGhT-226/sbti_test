from flask import Flask, render_template, request, jsonify
import sqlite3
import json

app = Flask(__name__)
application = app

# ===================== 1. 核心配置（题库、人格库，可自由扩展）=====================
question_list = [
    {
        "id": 1,
        "title": "早上起床的第一件事是？",
        "options": [
            {"text": "摸手机刷短视频，上班/上学迟到也不管", "score": {"摆烂大王": 2, "摸鱼专家": 1}},
            {"text": "猛地坐起，光速洗漱冲出门，主打一个极限卡点", "score": {"极限特种兵": 2, "摸鱼专家": 1}},
            {"text": "根本起不来，直接请假/旷课，继续睡", "score": {"摆烂大王": 3}}
        ]
    },
    {
        "id": 2,
        "title": "朋友约你出门，你的第一反应是？",
        "options": [
            {"text": "好耶！立刻收拾出门，社交能量拉满", "score": {"社交疯子": 3}},
            {"text": "找借口推脱，只想在家躺着，谁也别叫我", "score": {"宅家隐士": 3}},
            {"text": "先答应，出门前半小时临时说去不了", "score": {"鸽王本王": 3}}
        ]
    },
    {
        "id": 3,
        "title": "发了工资/生活费，你会？",
        "options": [
            {"text": "立刻全花光，主打一个月光族，一分不剩", "score": {"月光战神": 3}},
            {"text": "精打细算，存一半花一半，绝不乱花钱", "score": {"人间清醒": 3}},
            {"text": "先给朋友/对象买买买，自己剩多少无所谓", "score": {"散财童子": 3}}
        ]
    }
]

personality_list = {
    "摆烂大王": {"avatar": "😪", "desc": "你的SBTI人格是【摆烂大王】！人生信条是“能躺着绝不坐着，能拖着绝不做着”，主打一个与世无争，万物皆可摆烂。"},
    "摸鱼专家": {"avatar": "🐟", "desc": "你的SBTI人格是【摸鱼专家】！上班/上学的核心任务就是摸鱼，带薪拉屎、上班刷剧是你的日常操作。"},
    "极限特种兵": {"avatar": "⚡", "desc": "你的SBTI人格是【极限特种兵】！永远在卡点，永远在赶deadline，能一晚干完一周的活，主打一个极限压缩时间。"},
    "社交疯子": {"avatar": "🎉", "desc": "你的SBTI人格是【社交疯子】！天生的社牛达人，人越多越兴奋，朋友遍布五湖四海，主打一个社交能量无限。"},
    "宅家隐士": {"avatar": "🏠", "desc": "你的SBTI人格是【宅家隐士】！家就是你的快乐星球，床就是你的本命归宿，谁也别想把你从家里拽出去。"},
    "鸽王本王": {"avatar": "🕊️", "desc": "你的SBTI人格是【鸽王本王】！答应的事永远做不到，约好的局永远会放鸽子，你的口头禅是“下次一定”。"},
    "月光战神": {"avatar": "💰", "desc": "你的SBTI人格是【月光战神】！赚钱能力一般，花钱能力拉满，工资/生活费到账的那一刻，就已经规划好了全部去处。"},
    "人间清醒": {"avatar": "🧠", "desc": "你的SBTI人格是【人间清醒】！全网都在疯疯癫癫，只有你主打一个理性至上，不跟风不内耗，活成了一股难得的清流。"},
    "散财童子": {"avatar": "🎁", "desc": "你的SBTI人格是【散财童子】！对自己抠抠搜搜，对朋友/对象大方到极致，出门永远抢着买单，主打一个为爱发电。"}
}

# ===================== 2. 数据库初始化（SQLite，单文件存储，无需安装）=====================
def init_db():
    conn = sqlite3.connect('sbti.db')
    c = conn.cursor()
    # 创建表：存储用户测试结果
    c.execute('''CREATE TABLE IF NOT EXISTS test_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  personality TEXT, 
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# ===================== 3. 后端路由 =====================
@app.route('/')
def index():
    # 前端页面入口
    return render_template('index.html')

@app.route('/api/questions')
def get_questions():
    # 获取题库接口
    return jsonify(question_list)

@app.route('/api/submit', methods=['POST'])
def submit_test():
    # 提交答案、计算结果、存储数据接口
    data = request.json
    user_answers = data.get('answers', [])  # 用户选择的选项索引列表
    
    # 1. 计算用户得分
    user_score = {}
    for i, option_idx in enumerate(user_answers):
        question = question_list[i]
        option = question['options'][option_idx]
        for personality, score in option['score'].items():
            user_score[personality] = user_score.get(personality, 0) + score
    
    # 2. 匹配得分最高的人格
    max_score = 0
    result_personality = "人间清醒"
    for personality, score in user_score.items():
        if score > max_score:
            max_score = score
            result_personality = personality
    
    # 3. 存储结果到数据库
    conn = sqlite3.connect('sbti.db')
    c = conn.cursor()
    c.execute("INSERT INTO test_results (personality) VALUES (?)", (result_personality,))
    conn.commit()
    conn.close()
    
    # 4. 返回结果给前端
    return jsonify({
        'personality': result_personality,
        'avatar': personality_list[result_personality]['avatar'],
        'desc': personality_list[result_personality]['desc']
    })

@app.route('/api/stats')
def get_stats():
    # 运营数据统计接口：查看各人格测试人数
    conn = sqlite3.connect('sbti.db')
    c = conn.cursor()
    c.execute("SELECT personality, COUNT(*) as count FROM test_results GROUP BY personality ORDER BY count DESC")
    rows = c.fetchall()
    conn.close()
    stats = [{'personality': row[0], 'count': row[1]} for row in rows]
    return jsonify(stats)

if __name__ == '__main__':
    init_db()  # 启动时初始化数据库
    app.run(debug=True, port=5000)