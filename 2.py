import streamlit as st
from openai import OpenAI

# ===================== 1. 自定义配置（保留原Kimi API配置，无改动） =====================
# Kimi API 配置（Kimi为国内接口，无需代理）
KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-8k"  # 可选moonshot-v1-32k/moonshot-v1-128k

PROMPT_TEMPLATES = {
    "故事生成": {
        "template": "请以{主题}为核心，写一个{风格}风格的短篇故事，字数控制在{字数}字左右。要求情节完整，角色鲜明，语言流畅。",
        "params": ["主题", "风格", "字数"]
    },
    "营销文案": {
        "template": "为{产品名称}撰写{平台}平台的营销文案，突出{核心卖点}，语言风格{风格}，字数控制在{字数}字内。需吸引目标用户，激发购买欲。",
        "params": ["产品名称", "平台", "核心卖点", "风格", "字数"]
    },
    "论文提纲": {
        "template": "为《{论文题目}》（{学科}领域）设计详细提纲，逻辑清晰，结构完整，至少包含{章节数}个章节。需列出每个章节的核心研究内容和逻辑关联。",
        "params": ["论文题目", "学科", "章节数"]
    },
    "自由创作": {
        "template": "{用户输入}",
        "params": ["用户输入"]
    }
}


# ===================== 2. AI 生成核心函数（适配Streamlit，保留原校验和调用逻辑） =====================
def generate_content(kimi_api_key, template_type, param_dict):
    # 验证Kimi密钥
    if not kimi_api_key or not str(kimi_api_key).strip().startswith("sk-"):
        return "❌ 请输入有效的 Kimi API 密钥（以 sk- 开头）！"

    # 初始化Kimi客户端（国内接口，无需代理）
    try:
        client = OpenAI(
            api_key=kimi_api_key.strip(),
            base_url=KIMI_BASE_URL
        )
    except Exception as e:
        return f"❌ 客户端初始化失败：{str(e)}"

    # 获取模板和参数
    try:
        template_info = PROMPT_TEMPLATES[template_type]
        template = template_info["template"]
        required_params = template_info["params"]
    except KeyError:
        return "❌ 模板类型错误，无此生成模板！"

    # 校验参数（保留原有的数值/非空校验逻辑）
    invalid_or_missing = []
    for param in required_params:
        value = param_dict.get(param, "")
        if param in ["字数", "章节数"]:
            try:
                num_value = int(value) if value else 0
                if num_value <= 0:
                    invalid_or_missing.append(param)
            except (ValueError, TypeError):
                invalid_or_missing.append(param)
        else:
            if not str(value).strip():
                invalid_or_missing.append(param)

    if invalid_or_missing:
        return f"❌ 缺少或无效参数：{', '.join(invalid_or_missing)}（请填写有效且非空的内容）"

    # 调用Kimi API
    try:
        prompt = template.format(**param_dict)
        response = client.chat.completions.create(
            model=KIMI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=8192
        )
        return response.choices[0].message.content
    except Exception as e:
        error_info = str(e)
        if "invalid api key" in error_info.lower():
            return "❌ Kimi API密钥无效或已过期！"
        elif "insufficient funds" in error_info.lower():
            return "❌ Kimi账户余额不足，请充值！"
        else:
            return f"❌ 生成失败：{error_info}"


# ===================== 3. Streamlit 界面搭建（核心改写部分） =====================
def main():
    # 页面配置（Streamlit 专属，设置标题和图标）
    st.set_page_config(
        page_title="我的 AI 文字生成工具（Kimi版/Streamlit）",
        page_icon="📝",
        layout="wide"
    )

    # 页面标题和说明（替代 Gradio 的 gr.Markdown）
    st.title("📝 我的 AI 文字生成工具（Kimi版/Streamlit）")
    st.subheader("操作步骤：1. 输入Kimi API密钥 → 2. 选择模板 → 3. 填写参数 → 4. 生成文本")
    st.info(f"当前使用 Kimi {KIMI_MODEL} 模型（国内接口，无需代理）")
    st.divider()

    # 1. Kimi API 密钥输入（替代 Gradio 的 gr.Textbox，密码类型）
    kimi_api_key = st.text_input(
        label="Kimi API 密钥",
        type="password",
        placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        help="密钥从Kimi（月之暗面）官网获取，请勿泄露"
    )

    # 2. 模板选择下拉框（替代 Gradio 的 gr.Dropdown）
    template_type = st.selectbox(
        label="选择生成模板",
        options=list(PROMPT_TEMPLATES.keys()),
        index=0  # 默认选中第一个模板（故事生成）
    )

    st.divider()
    st.subheader("📋 填写模板参数")

    # 3. 根据选中模板，动态渲染对应的参数输入框（核心：替代 Gradio 的组件显隐逻辑）
    current_template = PROMPT_TEMPLATES[template_type]
    required_params = current_template["params"]
    param_dict = {}  # 存储用户填写的参数

    # 遍历当前模板的必填参数，渲染对应的输入组件
    for param in required_params:
        if param == "字数":
            # 数字输入框（整数、有范围限制，替代 Gradio 的 gr.Number）
            param_value = st.number_input(
                label=param,
                value=500,
                min_value=100,
                max_value=2000,
                step=10,
                help="请输入100-2000之间的整数"
            )
        elif param == "章节数":
            # 数字输入框（整数、有范围限制）
            param_value = st.number_input(
                label=param,
                value=5,
                min_value=3,
                max_value=10,
                step=1,
                help="请输入3-10之间的整数"
            )
        elif param == "用户输入":
            # 多行文本输入框（替代 Gradio 的 gr.Textbox(lines=5)）
            param_value = st.text_area(
                label=param,
                placeholder="请详细描述你的创作需求...",
                height=150
            )
        else:
            # 普通单行文本输入框
            param_value = st.text_input(
                label=param,
                placeholder=f"例如：{get_param_placeholder(param)}"
            )

        # 存储用户填写的参数值
        param_dict[param] = param_value

    st.divider()

    # 4. 生成按钮（替代 Gradio 的 gr.Button，Streamlit 采用「按钮触发逻辑」）
    if st.button("🚀 生成文本", type="primary", use_container_width=True):
        # 显示加载状态（提升用户体验，替代 Gradio 的自动加载）
        with st.spinner("正在调用 Kimi API 生成内容，请稍候..."):
            # 调用核心生成函数
            result = generate_content(kimi_api_key, template_type, param_dict)

            # 显示生成结果（替代 Gradio 的结果文本框）
            st.subheader("📄 生成结果")
            st.text_area(
                label="Kimi 模型输出",
                value=result,
                height=400,
                disabled=True,  # 结果不可编辑，仅展示
                help="结果仅供参考，可自行复制修改"
            )


# ===================== 辅助函数：为参数输入框提供占位提示 =====================
def get_param_placeholder(param):
    placeholders = {
        "主题": "友情、星空、冒险...",
        "风格": "治愈、悬疑、科幻、古风...",
        "产品名称": "无线蓝牙耳机、智能保温杯...",
        "平台": "微信朋友圈、抖音、小红书...",
        "核心卖点": "超长续航、便携小巧、健康环保...",
        "论文题目": "基于深度学习的图像识别技术研究...",
        "学科": "计算机科学与技术、汉语言文学..."
    }
    return placeholders.get(param, "")


# ===================== 运行 Streamlit 应用 =====================
if __name__ == "__main__":
    main()
