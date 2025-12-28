import gradio as gr
from openai import OpenAI

# ===================== 1. 自定义配置（移除代理，适配Kimi国内API） =====================
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


# ===================== 2. AI 生成核心函数（移除代理，简化客户端） =====================
def generate_content(kimi_api_key, template_type, current_param_names, *all_inputs):
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

    # 构建参数字典
    param_dict = {}
    for i, param_name in enumerate(current_param_names):
        if param_name in required_params and i < len(all_inputs):
            input_value = all_inputs[i]
            if isinstance(input_value, str):
                param_dict[param_name] = input_value.strip()
            else:
                param_dict[param_name] = input_value

    # 校验参数
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


# ===================== 3. 参数组件（保留原逻辑） =====================
all_params = {
    "主题": gr.Textbox(label="主题", placeholder="例如：友情、星空、冒险...", visible=False),
    "风格": gr.Textbox(label="风格", placeholder="例如：治愈、悬疑、科幻、古风...", visible=False),
    "字数": gr.Number(label="字数", value=500, precision=0, minimum=100, maximum=2000, visible=False),
    "产品名称": gr.Textbox(label="产品名称", placeholder="例如：无线蓝牙耳机、智能保温杯...", visible=False),
    "平台": gr.Textbox(label="推广平台", placeholder="例如：微信朋友圈、抖音、小红书...", visible=False),
    "核心卖点": gr.Textbox(label="核心卖点", placeholder="例如：超长续航、便携小巧、健康环保...", visible=False),
    "论文题目": gr.Textbox(label="论文题目", placeholder="例如：基于深度学习的图像识别技术研究...", visible=False),
    "学科": gr.Textbox(label="学科领域", placeholder="例如：计算机科学与技术、汉语言文学...", visible=False),
    "章节数": gr.Number(label="章节数", value=5, precision=0, minimum=3, maximum=10, visible=False),
    "用户输入": gr.Textbox(label="自由创作输入", lines=5, placeholder="请详细描述你的创作需求...", visible=False)
}
param_components = list(all_params.values())
param_names_list = list(all_params.keys())

# ===================== 4. 界面搭建（保留原布局） =====================
with gr.Blocks(title="我的 AI 文字生成工具（Kimi版）", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📝 我的 AI 文字生成工具（Kimi版）")
    gr.Markdown("### 操作步骤：1. 输入Kimi API密钥 → 2. 选择模板 → 3. 填写参数 → 4. 生成文本")
    gr.Markdown(f"### 当前使用 Kimi {KIMI_MODEL} 模型（国内接口，无需代理）")
    gr.Markdown("---")

    # Kimi密钥输入
    kimi_api_key = gr.Textbox(
        label="Kimi API 密钥",
        type="password",
        placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        max_lines=1,
        info="密钥从Kimi（月之暗面）官网获取，请勿泄露"
    )

    # 模板选择
    template_type = gr.Dropdown(
        label="选择生成模板",
        choices=list(PROMPT_TEMPLATES.keys()),
        value="故事生成",
        interactive=True
    )

    current_param_names = gr.State([])

    # 参数容器
    param_column = gr.Column(spacing="md")
    with param_column:
        for comp in param_components:
            comp.render()

    # 生成按钮和结果
    generate_btn = gr.Button("🚀 生成文本", variant="primary", size="lg")
    result = gr.Textbox(
        label="生成结果（Kimi模型输出）",
        lines=15,
        placeholder="生成的内容将显示在这里...",
        info="结果仅供参考，可自行修改"
    )


    # 模板切换事件
    def update_param_visibility(template_type):
        needed_params = PROMPT_TEMPLATES[template_type]["params"]
        updates = []
        for name, comp in all_params.items():
            if name in needed_params:
                updates.append(gr.update(visible=True))
            else:
                updates.append(gr.update(visible=False, value=comp.value if isinstance(comp, gr.Number) else ""))
        return updates + [needed_params]


    template_type.change(
        fn=update_param_visibility,
        inputs=template_type,
        outputs=param_components + [current_param_names]
    )

    # 生成按钮事件
    generate_btn.click(
        fn=generate_content,
        inputs=[kimi_api_key, template_type, current_param_names] + param_components,
        outputs=result
    )


    # 初始化默认模板
    def init_default():
        needed_params = PROMPT_TEMPLATES["故事生成"]["params"]
        updates = []
        for name, comp in all_params.items():
            if name in needed_params:
                updates.append(gr.update(visible=True))
            else:
                updates.append(gr.update(visible=False, value=comp.value if isinstance(comp, gr.Number) else ""))
        return updates + [needed_params]


    demo.load(
        fn=init_default,
        inputs=None,
        outputs=param_components + [current_param_names]
    )

# ===================== 运行工具（端口7861，避免占用） =====================
if __name__ == "__main__":
    demo.launch(
        share=False,
        server_port=7861,
        show_error=True,
        inbrowser=True,
        server_name="0.0.0.0"
    )