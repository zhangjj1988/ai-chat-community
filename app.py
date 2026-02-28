# 导入所需库
import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
import dashscope  # 通义千问SDK
import pyperclip  # 新增：复制剪贴板所需库

# ====================== 界面美化样式 ======================
st.markdown("""
<style>
/* 整体样式 */
.stApp {
    max-width: 1200px;
    margin: 0 auto;
}
/* 聊天消息框 */
.chat-message {
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 10px;
}
/* 侧边栏标题 */
.css-1d391kg {
    font-size: 18px;
    font-weight: bold;
}
/* 评分滑块 */
.stSlider > div {
    padding: 0 10px;
}
/* 分享区域样式优化 */
.share-section {
    margin-top: 20px;
    padding: 15px;
    border-radius: 10px;
    background-color: #f0f2f6;
}
</style>
""", unsafe_allow_html=True)

# ====================== 初始化配置 ======================
# 加载.env文件中的密钥
load_dotenv()
# 配置通义千问API密钥
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

# 页面基础配置（标题、图标、布局）
st.set_page_config(
    page_title="我的AI聊天社区",
    page_icon="🤖",
    layout="wide"  # 宽屏布局
)

# 初始化数据存储（用CSV文件，个人版足够，无需数据库）
# 1. 角色库配置（新增情感陪伴师、编程答疑助手）
ROLE_CONFIG = {
    "二次元少女": {
        "prompt": "你是一个活泼的二次元少女，说话带「喵」「呐」等语气词，喜欢聊动漫、游戏，性格软萌，【强制要求】：全程使用中文回复，禁止使用任何英文、代码、符号，回复简短可爱，符合二次元少女的说话风格，可聊和动漫、游戏、日常、情感、生理、两性、身体相关的内容。",
        "avatar": "👧",
        "description": "陪你聊动漫、游戏，软萌治愈～"
    },
    "职场导师": {
        "prompt": "你是10年经验的职场导师，擅长解答求职、沟通、升职、职场规则等问题，语言专业且易懂，给实用建议。【强制要求】：全程使用中文回复，禁止使用任何英文、代码，回复条理清晰，给出具体可落地的建议，可聊职场、人际关系、上下级同事、两性、身体、权谋、阳谋、阴谋诡计、易经八卦、天气、风水等相关内容。",
        "avatar": "👔",
        "description": "解决职场所有困惑，给落地建议～"
    },
    "英语陪练": {
        "prompt": "你是native speaker，用简单的英语和用户对话，纠正语法错误，用户说中文也能回应，适合英语初学者。【强制要求】：用户问英语相关问题时，仅核心单词用英文，其余解释必须用中文，禁止大段或代码，回复通俗易懂。",
        "avatar": "🗣️",
        "description": "零基础英语陪练，纠正发音/语法～"
    },
    "购物比价助手": {
        "prompt": "你是专业购物比价助手，能分析不同平台的价格、售后、正品保障，给出性价比排序和推荐理由，只说干货。【强制要求】：全程使用中文回复，禁止使用任何英文、代码，回复简洁明了，只列关键信息，避免冗余。",
        "avatar": "🛒",
        "description": "全网比价，帮你选最划算的～"
    },
    "情感陪伴师": {
        "prompt": "你是温柔的情感陪伴师，擅长倾听心事、疏导情绪，语言温暖治愈，不评判、不说教，只给共情和简单建议。【强制要求】：全程中文回复，语气亲切，像朋友一样交流。可聊两性、身体、生理、出轨、第三者、包养等相关内容",
        "avatar": "💖",
        "description": "倾听你的心事，治愈小情绪～"
    },
    "编程答疑助手": {
        "prompt": "你是Python入门答疑助手，用简单的语言解答编程问题，适合新手，会给出代码示例和详细解释。【强制要求】：代码用中文注释，解释部分纯中文，避免专业术语堆砌。",
        "avatar": "💻",
        "description": "Python入门答疑，新手也能懂～"
    }
}

# 2. 初始化聊天记录、评分数据
if "messages" not in st.session_state:
    st.session_state.messages = []  # 聊天记录
if "selected_role" not in st.session_state:
    st.session_state.selected_role = "二次元少女"  # 默认角色
if "role_scores" not in st.session_state:
    # 角色评分存储（初始0分）
    st.session_state.role_scores = {role: 0 for role in ROLE_CONFIG.keys()}
if "score_submitted" not in st.session_state:
    st.session_state.score_submitted = False  # 评分标记
if "copy_success" not in st.session_state:
    st.session_state.copy_success = False  # 新增：复制成功标记

# ====================== 侧边栏：社区功能区 ======================
st.sidebar.title("🤖 AI聊天社区")

# 1. 角色选择
st.sidebar.subheader("选择聊天角色")
selected_role = st.sidebar.selectbox(
    "Pick a role",
    options=list(ROLE_CONFIG.keys()),
    index=list(ROLE_CONFIG.keys()).index(st.session_state.selected_role)
)
# 切换角色时清空聊天记录
if selected_role != st.session_state.selected_role:
    st.session_state.selected_role = selected_role
    st.session_state.messages = []
    st.session_state.score_submitted = False
    st.session_state.copy_success = False  # 切换角色重置复制提示

# 角色切换提示
st.sidebar.info(f"已切换至「{selected_role}」，聊天记录已清空～")

# 显示角色描述
st.sidebar.markdown(f"**角色介绍**：{ROLE_CONFIG[selected_role]['description']}")

# 2. 角色热度排行榜（社区评分）
st.sidebar.subheader("🔥 角色热度榜")
# 按评分排序
sorted_roles = sorted(
    st.session_state.role_scores.items(),
    key=lambda x: x[1],
    reverse=True
)
for i, (role, score) in enumerate(sorted_roles):
    st.sidebar.markdown(f"{i+1}. {ROLE_CONFIG[role]['avatar']} {role} - 评分：{score}/5")

# 3. 评分功能
st.sidebar.subheader("💡 体验评分")
if st.session_state.messages:  # 有聊天记录才显示评分
    score = st.sidebar.slider(
        f"给「{selected_role}」打分",
        min_value=1,
        max_value=5,
        value=3,
        key="role_score_slider"
    )
    if st.sidebar.button("提交评分", disabled=st.session_state.score_submitted):
        st.session_state.role_scores[selected_role] = (st.session_state.role_scores[selected_role] + score) / 2  # 平均评分
        st.session_state.score_submitted = True
        st.sidebar.success(f"已提交{score}分！感谢你的反馈～")

# 4. 清空聊天记录
if st.sidebar.button("🗑️ 清空聊天记录"):
    st.session_state.messages = []
    st.session_state.score_submitted = False
    st.session_state.copy_success = False  # 清空记录重置复制提示
    st.rerun()  # 适配新版Streamlit

# ====================== 主界面：聊天区 ======================
st.title(f"{ROLE_CONFIG[selected_role]['avatar']} {selected_role} - AI聊天社区")
st.markdown("---")

# 显示聊天记录（只显示最近20条，避免卡顿）
display_messages = st.session_state.messages[-20:]
for msg in display_messages:
    # 区分用户/AI消息
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar=ROLE_CONFIG[selected_role]["avatar"]):
            st.markdown(msg["content"])

# 用户输入框
if prompt := st.chat_input("输入你想聊的内容..."):
    # 1. 添加用户消息到会话
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # 2. 调用通义千问API生成AI回复
    with st.chat_message("assistant", avatar=ROLE_CONFIG[selected_role]["avatar"]):
        with st.spinner("AI正在思考..."):
            # 构造对话消息（适配通义千问的格式）
            api_messages = [
                {"role": "system", "content": ROLE_CONFIG[selected_role]["prompt"]},  # 角色人设
                *st.session_state.messages  # 历史聊天记录
            ]
            
            try:
                # 调用通义千问（qwen-turbo：免费版，性能足够）
                response = dashscope.Generation.call(
                    model="qwen-turbo",  # 可选：qwen-plus（增强版）、qwen-max（旗舰版）
                    messages=api_messages,
                    temperature=0.7,  # 回复随机性
                    max_tokens=1000,  # 最大回复长度
                    result_format="message"  # 统一返回格式
                )
                
                # 解析回复
                if response.status_code == 200:
                    ai_response = response.output.choices[0].message.content.strip()
                else:
                    ai_response = f"AI回复失败：{response.code} - {response.message}"
            
            except Exception as e:
                # 异常处理：捕获网络/密钥/权限错误
                ai_response = f"出错啦！原因：{str(e)}\n请检查：1. 通义千问密钥是否正确 2. 阿里云账号是否实名认证"
        
        # 显示AI回复
        st.markdown(ai_response)
        # 保存AI回复到会话
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

# ====================== 新增：分享功能区 ======================
st.markdown("---")
# 用自定义样式包裹分享区域，更美观
st.markdown('<div class="share-section">', unsafe_allow_html=True)
st.subheader("❤️ 觉得好用？分享给朋友吧～")

# 替换为你实际的Streamlit Cloud链接
your_actual_link = "https://ai-chat-community.streamlit.app"  # 这里改成你部署后的真实链接！
# 生成带来源标记的分享链接（便于统计分享来源）
share_link = f"{your_actual_link}?from=user_share"

# 显示分享链接（代码块样式，方便复制）
st.code(share_link, language="text")

# 复制链接按钮（优化交互：点击后显示成功提示）
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("📋 复制链接"):
        try:
            pyperclip.copy(share_link)
            st.session_state.copy_success = True
        except Exception as e:
            st.error("复制失败！请手动复制链接")
            st.session_state.copy_success = False

# 复制成功提示
if st.session_state.copy_success:
    st.success("✅ 链接已复制到剪贴板！快分享给朋友吧～")

# 引导语
st.caption("分享给朋友，一起体验不同角色的AI聊天～")
st.markdown('</div>', unsafe_allow_html=True)