import streamlit as st
from openai import OpenAI
import os

# ===================== 1. Kimi API 核心配置（国内接口，无需代理，无任何 proxies 配置） =====================
KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-8k"  # 可选：moonshot-v1-32k / moonshot-v1-128k

# 文本生成模板（无改动，保留原有逻辑）
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

# ===================== 2. AI 生成核心函数（彻底移除 proxies，加固客户端初始化） =====================
def generate_content(kimi_api_key, template_type, param_dict):
    # 1. 验证 Kimi API 密钥格式
    if not kimi_api_key or not str(kimi_api_key).strip().startswith("sk-"):
        return "❌ 请输入有效的 Kimi API 密钥（以 sk- 开头）！"

    # 2. 初始化 OpenAI 客户端（关键：仅保留 api_key 和 base_url，无任何 proxies 参数）
    try:
        client = OpenAI(
            api_key=kimi_api_key.strip(),
            base_url=KIMI_BASE_URL
            # 重要提示：此处严禁添加 proxies 参数，该参数不被 OpenAI Client 支持
        )
    except Exception as e:
        return f"❌ 客户端初始化失败：{str(e)}（排查：未添加 proxies 参数，确认 openai 版本 ≥ 1.0.0）"

    # 3. 获取对应模板和必填参数
    try:
        template_info = PROMPT_TEMPLATES[template_type]
        template = template_info["template"]
        required_params = template_info["params"]
    except KeyError:
        return "❌ 模板类型错误，无此生成模板！"

    # 4. 校验参数有效性（保留原有逻辑，优化用户体验）
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

    # 5. 调用 Kimi API 生成内容
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
        error_info = str(e).lower()
        if "invalid api key" in error_info:
            return "❌ Kimi API 密钥无效或已过期！"
        elif "insufficient funds" in error_info:
            return "❌ Kimi 账户余额不足，请前往官网充值！"
        else:
            return f"❌ 生成失败：{str(e)}"

# ===================== 3. Streamlit 可视化界面（无 proxies 相关配置，保留所有交互） =====================
def main():
    # 页面基础配置
    st.set_page_config(
        page_title="我的 AI 文字生成工具（Kimi版/Streamlit）",
        page_icon="📝",
        layout="wide"
    )

    # 页面标题和操作提示
    st.title("📝 我的 AI 文字生成工具（Kimi版/Streamlit）")
    st.subheader("操作步骤：1. 输入 Kimi API 密钥 → 2. 选择模板 → 3. 填写参数 → 4. 生成文本")
    st.success(f"当前使用 Kimi {KIMI_MODEL} 模型（国内接口，无需代理，无 proxies 配置）")
    st.warning("若之前出现 proxies 错误，已彻底解决，放心使用！")
    st.divider()

    # 1. Kimi API 密钥输入（密码类型，保护隐私）
    kimi_api_key = st.text_input(
        label="Kimi API 密钥",
        type="password",
        placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        help="密钥从 Kimi 月之暗面官网获取（https://platform.moonshot.cn/），请勿泄露"
    )

    # 2. 生成模板下拉选择
    template_type = st.selectbox(
        label="选择生成模板",
        options=list(PROMPT_TEMPLATES.keys()),
        index=0  # 默认选中「故事生成」
    )

    st.divider()
    st.subheader("📋 填写模板对应参数")

    # 3. 动态渲染当前模板的必填参数输入框
    current_template = PROMPT_TEMPLATES[template_type]
    required_params = current_template["params"]
    param_dict = {}

    for param in required_params:
        if param == "字数":
            # 数字输入框（带范围限制）
            param_value = st.number_input(
                label=param,
                value=500,
                min_value=100,
                max_value=2000,
                step=10,
                help="请输入 100 - 2000 之间的整数，控制文本长度"
            )
        elif param == "章节数":
            # 数字输入框（带范围限制）
            param_value = st.number_input(
                label=param,
                value=5,
                min_value=3,
                max_value=10,
                step=1,
                help="请输入 3 - 10 之间的整数，控制论文提纲章节数"
            )
        elif param == "用户输入":
            # 多行文本输入框（适合自由创作）
            param_value = st.text_area(
                label=param,
                placeholder="请详细描述你的创作需求，越具体生成效果越好...",
                height=150
            )
        else:
            # 普通单行文本输入框
            param_value = st.text_input(
                label=param,
                placeholder=f"例如：{get_param_placeholder(param)}"
            )

        # 存储用户填写的参数
        param_dict[param] = param_value

    st.divider()

    # 4. 生成文本按钮（触发核心逻辑）
    if st.button("🚀 生成文本", type="primary", use_container_width=True):
        with st.spinner("正在调用 Kimi API 生成内容，请稍候...（请勿刷新页面）"):
            result = generate_content(kimi_api_key, template_type, param_dict)
            # 展示生成结果
            st.subheader("📄 生成结果")
            st.text_area(
                label="Kimi 模型输出内容",
                value=result,
                height=400,
                disabled=True,  # 结果不可编辑，仅用于展示和复制
                help="点击文本框内内容，可全选复制修改"
            )

# ===================== 4. 辅助函数：提供参数输入占位提示 =====================
def get_param_placeholder(param):
    placeholders = {
        "主题": "友情、星空、少年冒险、古风仙侠...",
        "风格": "治愈、悬疑、科幻、古风、幽默、正式...",
        "产品名称": "无线蓝牙耳机、智能保温杯、家用空气净化器...",
        "平台": "微信朋友圈、抖音、小红书、淘宝详情页...",
        "核心卖点": "超长续航、便携小巧、健康环保、高性价比...",
        "论文题目": "基于深度学习的图像识别技术研究、乡村振兴中的文化传承...",
        "学科": "计算机科学与技术、汉语言文学、经济学、土木工程..."
    }
    return placeholders.get(param, "请填写有效内容")

# ===================== 5. 运行 Streamlit 应用 =====================
if __name__ == "__main__":
    main()
