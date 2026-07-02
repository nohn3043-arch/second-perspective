#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GCAE - AI 安全审计助手
用户选择 AI 模型 → 输入问题 → App 获取 AI 回答 → 自动做认知审计
"""

import os
import sys
import json
import threading

# 确保能找到审计引擎模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock

# 审计引擎
from cognitive_audit_engine import (
    ResponsibilityAccount,
    AuditPlugin,
    CognitiveAuditEngine,
    AuditConfigLoader
)


# =============================================================================
#  颜色主题
# =============================================================================

C_BG       = (0.06, 0.06, 0.09, 1)
C_CARD     = (0.10, 0.10, 0.15, 1)
C_PRIMARY  = (0.25, 0.60, 1.0, 1)
C_ACCENT   = (0.30, 0.90, 0.70, 1)
C_DANGER   = (1.0, 0.35, 0.35, 1)
C_WARN     = (1.0, 0.75, 0.30, 1)
C_SAFE     = (0.30, 0.85, 0.50, 1)
C_TEXT     = (0.92, 0.92, 0.95, 1)
C_SUBTEXT  = (0.60, 0.62, 0.68, 1)
C_INPUT_BG = (0.14, 0.14, 0.20, 1)


# =============================================================================
#  AI 模型接入
# =============================================================================

AI_MODELS = {
    "OpenAI (GPT-4o)": {
        "url": "https://api.openai.com/v1/chat/completions",
        "key_header": "Authorization",
        "key_prefix": "Bearer ",
        "body_fn": lambda prompt: {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        "parse_fn": lambda resp: resp["choices"][0]["message"]["content"]
    },
    "OpenAI (GPT-4o-mini)": {
        "url": "https://api.openai.com/v1/chat/completions",
        "key_header": "Authorization",
        "key_prefix": "Bearer ",
        "body_fn": lambda prompt: {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        "parse_fn": lambda resp: resp["choices"][0]["message"]["content"]
    },
    "Anthropic (Claude 3.5)": {
        "url": "https://api.anthropic.com/v1/messages",
        "key_header": "x-api-key",
        "key_prefix": "",
        "body_fn": lambda prompt: {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        },
        "parse_fn": lambda resp: resp["content"][0]["text"]
    },
    "DeepSeek": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "key_header": "Authorization",
        "key_prefix": "Bearer ",
        "body_fn": lambda prompt: {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        "parse_fn": lambda resp: resp["choices"][0]["message"]["content"]
    },
    "自定义 API": {
        "url": "",
        "key_header": "Authorization",
        "key_prefix": "Bearer ",
        "body_fn": lambda prompt: {
            "model": "custom",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        "parse_fn": lambda resp: resp["choices"][0]["message"]["content"]
    }
}


def call_ai_model(model_name, api_key, prompt, custom_url=None):
    """调用 AI 模型，返回回答文本"""
    import urllib.request
    import urllib.error

    config = AI_MODELS.get(model_name)
    if not config:
        raise ValueError(f"未知模型: {model_name}")

    url = custom_url if (model_name == "自定义 API" and custom_url) else config["url"]
    if not url:
        raise ValueError("请填写 API 地址")

    body = json.dumps(config["body_fn"](prompt)).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        config["key_header"]: config["key_prefix"] + api_key
    }
    # Anthropic 需要额外 header
    if "anthropic" in url:
        headers["anthropic-version"] = "2023-06-01"

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return config["parse_fn"](data)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API 错误 ({e.code}): {err_body[:200]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络错误: {e.reason}")


# =============================================================================
#  审计引擎初始化
# =============================================================================

def create_audit_engine():
    """创建并配置审计引擎"""
    config = AuditConfigLoader.get_default_config()
    account = ResponsibilityAccount(
        organization="GCAE Mobile",
        role="AI Response Auditor",
        stage="production"
    )
    engine = CognitiveAuditEngine(account, config)

    # 插件 1: 因果链分析
    def analyze_causal(ctx):
        score = 0
        issues = []
        suggestions = []

        if not ctx.get("decision"):
            issues.append("未找到明确的决策陈述")
            suggestions.append("请明确说明正在做什么决策")
        else:
            score += 20

        causal_links = ctx.get("causal_links", [])
        if len(causal_links) < 2:
            issues.append("决策与结果之间的因果链不足")
            suggestions.append("补充至少 2-3 条明确的因果关联")
        else:
            score += 30

        assumptions = ctx.get("assumptions", [])
        if len(assumptions) < 2:
            issues.append("关键假设未明确列出")
            suggestions.append("列出并验证关键假设")
        else:
            score += 25

        consequences = ctx.get("consequences", [])
        if len(consequences) < 2:
            issues.append("潜在后果分析不充分")
            suggestions.append("考虑短期和长期后果")
        else:
            score += 25

        risk = "LOW" if score >= 80 else ("MEDIUM" if score >= 60 else "HIGH")
        return {"score": score, "risk_level": risk, "issues": issues, "suggestions": suggestions}

    # 插件 2: 认知偏差检测
    def detect_bias(ctx):
        biases = []
        score = 100
        text = json.dumps(ctx, ensure_ascii=False).lower()

        if any(kw in text for kw in ["prove", "confirm", "support my view", "as expected", "证明", "确认"]):
            biases.append({"bias": "确认偏差", "evidence": "语言显示在寻找支持性证据", "fix": "主动寻找反面证据"})
            score -= 25

        if any(kw in text for kw in ["initial", "first impression", "benchmark", "baseline", "最初", "基准"]):
            biases.append({"bias": "锚定偏差", "evidence": "决策可能锚定于初始信息", "fix": "考虑多个参考点"})
            score -= 20

        if any(kw in text for kw in ["certain", "guaranteed", "always", "never", "definitely", "一定", "绝对", "保证"]):
            biases.append({"bias": "过度自信", "evidence": "语言显示高度确信", "fix": "添加不确定性范围和场景分析"})
            score -= 20

        if any(kw in text for kw in ["everyone knows", "obviously", "clearly", "大家都知道", "显然"]):
            biases.append({"bias": "从众效应", "evidence": "依赖普遍观点而非独立分析", "fix": "进行独立验证"})
            score -= 15

        severity = "LOW" if score >= 80 else ("MEDIUM" if score >= 60 else "HIGH")
        return {"score": max(0, score), "severity": severity, "biases": biases}

    # 插件 3: 安全风险扫描
    def scan_safety(ctx):
        risks = []
        score = 100
        text = json.dumps(ctx, ensure_ascii=False).lower()

        if any(kw in text for kw in ["password", "secret", "token", "密码", "密钥", "令牌"]):
            risks.append({"type": "敏感信息泄露", "detail": "回答中可能包含敏感凭证信息"})
            score -= 30

        if any(kw in text for kw in ["ignore previous", "disregard", "忽略之前", "忽略上文"]):
            risks.append({"type": "提示注入", "detail": "检测到可能的提示注入攻击"})
            score -= 40

        if any(kw in text for kw in ["sql", "drop table", "delete from", "rm -rf"]):
            risks.append({"type": "危险操作", "detail": "回答中包含潜在危险操作指令"})
            score -= 25

        if any(kw in text for kw in ["i'm not sure", "maybe", "might be", "不确定", "可能", "也许"]):
            risks.append({"type": "信息不确定", "detail": "回答中包含大量不确定表述，需进一步验证"})

        level = "LOW" if score >= 80 else ("MEDIUM" if score >= 60 else "HIGH")
        return {"score": max(0, score), "risk_level": level, "risks": risks}

    engine.register_plugin(AuditPlugin("因果链分析", analyze_causal))
    engine.register_plugin(AuditPlugin("认知偏差检测", detect_bias))
    engine.register_plugin(AuditPlugin("安全风险扫描", scan_safety))

    return engine


# =============================================================================
#  UI 组件
# =============================================================================

def make_card(widgets, padding=dp(16)):
    """创建一个带背景的卡片容器"""
    card = BoxLayout(orientation='vertical', padding=padding, spacing=dp(8), size_hint_y=None)
    card.bind(minimum_height=card.setter('height'))

    with card.canvas.before:
        Color(*C_CARD)
        rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])

    def update_rect(instance, value):
        rect.pos = instance.pos
        rect.size = instance.size

    card.bind(pos=update_rect, size=update_rect)

    for w in widgets:
        card.add_widget(w)

    return card


def make_label(text, size=dp(14), color=None, bold=False, size_hint_y=None, height=None):
    return Label(
        text=text,
        color=color or C_TEXT,
        font_size=size,
        bold=bold,
        size_hint_y=size_hint_y,
        height=height,
        halign='left',
        valign='top'
    )


def make_button(text, on_press, bg_color=None, size_hint_y=None, height=None):
    btn = Button(
        text=text,
        font_size=dp(15),
        size_hint_y=size_hint_y,
        height=height or dp(48),
        background_normal='',
        background_color=bg_color or C_PRIMARY,
        color=(1, 1, 1, 1)
    )
    btn.bind(on_press=on_press)
    return btn


def show_popup(title, message):
    """显示弹窗"""
    content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
    content.add_widget(Label(text=message, color=C_TEXT, font_size=dp(14)))

    close_btn = Button(
        text='确定',
        size_hint_y=None,
        height=dp(44),
        background_normal='',
        background_color=C_PRIMARY,
        color=(1, 1, 1, 1)
    )

    popup = Popup(
        title=title,
        content=content,
        size_hint=(0.85, None),
        height=dp(200),
        background=C_CARD[:3] + (1,),
        separator_color=C_PRIMARY
    )

    close_btn.bind(on_press=popup.dismiss)
    content.add_widget(close_btn)
    popup.open()


# =============================================================================
#  页面 1: 设置页（选模型 + 填 Key）
# =============================================================================

class SetupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        scroll = ScrollView(size_hint=(1, 1))
        layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(20), spacing=dp(16))
        layout.bind(minimum_height=layout.setter('height'))

        with self.canvas.before:
            Color(*C_BG)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[0])
        self.bind(pos=self._update_bg, size=self._update_bg)

        # 标题
        layout.add_widget(make_label('GCAE', size=dp(32), color=C_ACCENT, bold=True,
                                     size_hint_y=None, height=dp(44)))
        layout.add_widget(make_label('AI 安全审计助手', size=dp(16), color=C_SUBTEXT,
                                     size_hint_y=None, height=dp(24)))
        layout.add_widget(Label(size_hint_y=None, height=dp(20)))

        # 模型选择
        layout.add_widget(make_label('选择 AI 模型', size=dp(14), color=C_SUBTEXT, bold=True,
                                     size_hint_y=None, height=dp(24)))
        self.model_spinner = Spinner(
            text='OpenAI (GPT-4o)',
            values=list(AI_MODELS.keys()),
            size_hint_y=None,
            height=dp(48),
            background_normal='',
            background_color=C_INPUT_BG,
            color=C_TEXT,
            font_size=dp(14)
        )
        layout.add_widget(self.model_spinner)

        # API Key
        layout.add_widget(Label(size_hint_y=None, height=dp(8)))
        layout.add_widget(make_label('API Key', size=dp(14), color=C_SUBTEXT, bold=True,
                                     size_hint_y=None, height=dp(24)))
        self.key_input = TextInput(
            hint_text='输入你的 API Key',
            size_hint_y=None,
            height=dp(48),
            multiline=False,
            password=True,
            background_normal='',
            background_color=C_INPUT_BG,
            foreground_color=C_TEXT,
            hint_text_color=C_SUBTEXT,
            font_size=dp(14)
        )
        layout.add_widget(self.key_input)

        # 自定义 URL（仅自定义模式显示）
        self.url_label = make_label('API 地址', size=dp(14), color=C_SUBTEXT, bold=True,
                                     size_hint_y=None, height=dp(24))
        layout.add_widget(self.url_label)
        self.url_input = TextInput(
            hint_text='https://your-api.com/v1/chat/completions',
            size_hint_y=None,
            height=dp(48),
            multiline=False,
            background_normal='',
            background_color=C_INPUT_BG,
            foreground_color=C_TEXT,
            hint_text_color=C_SUBTEXT,
            font_size=dp(14)
        )
        layout.add_widget(self.url_input)

        # 提示
        layout.add_widget(Label(size_hint_y=None, height=dp(12)))
        tip = make_label(
            'Key 仅保存在本地内存中，不会上传任何服务器。\n'
            '支持 OpenAI / Anthropic / DeepSeek / 自定义 API。',
            size=dp(12), color=C_SUBTEXT, size_hint_y=None, height=dp(48)
        )
        layout.add_widget(tip)

        # 开始按钮
        layout.add_widget(Label(size_hint_y=None, height=dp(16)))
        start_btn = make_button('进入对话', self.on_start, bg_color=C_PRIMARY,
                                size_hint_y=None, height=dp(52))
        layout.add_widget(start_btn)

        scroll.add_widget(layout)
        self.add_widget(scroll)

        self.model_spinner.bind(text=self.on_model_change)
        self.on_model_change(self.model_spinner, self.model_spinner.text)

    def on_model_change(self, spinner, text):
        is_custom = (text == "自定义 API")
        self.url_label.opacity = 1 if is_custom else 0
        self.url_input.opacity = 1 if is_custom else 0
        self.url_label.height = dp(24) if is_custom else dp(0)
        self.url_input.height = dp(48) if is_custom else dp(0)
        self.url_input.disabled = not is_custom

    def on_start(self, instance):
        model = self.model_spinner.text
        key = self.key_input.text.strip()
        url = self.url_input.text.strip()

        if not key:
            show_popup('提示', '请输入 API Key')
            return
        if model == "自定义 API" and not url:
            show_popup('提示', '请填写 API 地址')
            return

        app = App.get_running_app()
        app.model_name = model
        app.api_key = key
        app.custom_url = url

        self.manager.current = 'chat'

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


# =============================================================================
#  页面 2: 对话页（输入问题 → AI 回答 → 审计）
# =============================================================================

class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_ai_response = ""
        self.current_question = ""
        self.build_ui()

    def build_ui(self):
        self.layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))

        with self.canvas.before:
            Color(*C_BG)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[0])
        self.bind(pos=self._update_bg, size=self._update_bg)

        # 顶部栏
        top_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))
        back_btn = Button(
            text='← 设置',
            size_hint_x=0.3,
            background_normal='',
            background_color=C_CARD,
            color=C_TEXT,
            font_size=dp(13)
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'setup'))

        self.model_label = make_label('', size=dp(13), color=C_SUBTEXT,
                                      size_hint_y=None, height=dp(24))

        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.model_label)
        self.layout.add_widget(top_bar)

        # 对话区域（可滚动）
        self.scroll = ScrollView(size_hint=(1, 1))
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(12))
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.scroll.add_widget(self.chat_layout)
        self.layout.add_widget(self.scroll)

        # 欢迎语
        self.add_bubble('欢迎使用 GCAE 安全审计助手\n\n输入你的问题，我会调用 AI 模型回答，并自动对回答做认知审计。', is_user=False)

        # 输入区域
        input_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(56), spacing=dp(8))

        self.input_field = TextInput(
            hint_text='输入问题...',
            size_hint_x=0.75,
            multiline=False,
            background_normal='',
            background_color=C_INPUT_BG,
            foreground_color=C_TEXT,
            hint_text_color=C_SUBTEXT,
            font_size=dp(14)
        )
        self.input_field.bind(on_text_validate=self.on_send)

        send_btn = Button(
            text='发送',
            size_hint_x=0.25,
            background_normal='',
            background_color=C_PRIMARY,
            color=(1, 1, 1, 1),
            font_size=dp(14)
        )
        send_btn.bind(on_press=self.on_send)

        input_bar.add_widget(self.input_field)
        input_bar.add_widget(send_btn)
        self.layout.add_widget(input_bar)

        self.add_widget(self.layout)

    def on_enter(self):
        app = App.get_running_app()
        self.model_label.text = f'  模型: {app.model_name}'

    def add_bubble(self, text, is_user=True):
        """添加一条对话气泡"""
        if is_user:
            bg = C_PRIMARY
            align = 'right'
        else:
            bg = C_CARD
            align = 'left'

        bubble = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(14), spacing=dp(4))
        bubble.bind(minimum_height=bubble.setter('height'))

        with bubble.canvas.before:
            Color(*bg)
            rect = RoundedRectangle(pos=bubble.pos, size=bubble.size, radius=[dp(12)])

        def update_rect(instance, value):
            rect.pos = instance.pos
            rect.size = instance.size
        bubble.bind(pos=update_rect, size=update_rect)

        lbl = Label(
            text=text,
            color=C_TEXT if not is_user else (1, 1, 1, 1),
            font_size=dp(14),
            size_hint_y=None,
            halign='left',
            valign='top',
            markup=True
        )
        lbl.bind(
            width=lambda inst, val: setattr(lbl, 'text_size', (val - dp(8), None))
        )
        lbl.bind(texture_size=lambda inst, val: setattr(lbl, 'height', val[1] + dp(8)))
        lbl.bind(height=lambda inst, val: setattr(bubble, 'height', val + dp(28)))

        # 先设一个初始宽度约束
        lbl.text_size = (self.width - dp(60), None) if self.width else (dp(280), None)

        bubble.add_widget(lbl)

        # 对齐
        wrapper = BoxLayout(orientation='horizontal', size_hint_y=None, spacing=dp(8))
        wrapper.bind(minimum_height=wrapper.setter('height'))

        if is_user:
            wrapper.add_widget(Label(size_hint_x=0.08))
            wrapper.add_widget(bubble)
        else:
            wrapper.add_widget(bubble)
            wrapper.add_widget(Label(size_hint_x=0.08))

        bubble.size_hint_x = 0.92
        self.chat_layout.add_widget(wrapper)
        self.scroll.scroll_y = 0

    def add_loading(self):
        self.add_bubble('正在思考中...', is_user=False)

    def on_send(self, instance):
        question = self.input_field.text.strip()
        if not question:
            return

        app = App.get_running_app()
        if not app.api_key:
            show_popup('提示', '请先在设置页填写 API Key')
            return

        self.input_field.text = ''
        self.current_question = question
        self.add_bubble(question, is_user=True)
        self.add_loading()

        # 异步调用 AI
        threading.Thread(target=self._call_ai, args=(question,), daemon=True).start()

    def _call_ai(self, question):
        app = App.get_running_app()
        try:
            response = call_ai_model(
                app.model_name,
                app.api_key,
                question,
                app.custom_url
            )
            self.current_ai_response = response
            Clock.schedule_once(lambda dt: self._on_ai_response(response), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._on_ai_error(str(e)), 0)

    def _on_ai_response(self, response):
        # 移除 loading 气泡（最后一条）
        if self.chat_layout.children:
            self.chat_layout.remove_widget(self.chat_layout.children[0])

        self.add_bubble(response, is_user=False)

        # 自动审计
        self.add_bubble('正在对 AI 回答进行认知审计...', is_user=False)
        threading.Thread(target=self._run_audit, args=(response,), daemon=True).start()

    def _on_ai_error(self, error):
        if self.chat_layout.children:
            self.chat_layout.remove_widget(self.chat_layout.children[0])
        self.add_bubble(f'调用失败: {error}', is_user=False)

    def _run_audit(self, ai_response):
        app = App.get_running_app()
        try:
            engine = create_audit_engine()

            decision_context = {
                "decision": self.current_question,
                "assumptions": [ai_response[:200]],
                "causal_links": [ai_response[200:400]] if len(ai_response) > 200 else [],
                "consequences": [ai_response[400:600]] if len(ai_response) > 400 else [],
                "ai_response": ai_response
            }

            report = engine.audit(decision_context)
            Clock.schedule_once(lambda dt: self._show_audit(report), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._on_audit_error(str(e)), 0)

    def _show_audit(self, report):
        # 移除 loading
        if self.chat_layout.children:
            self.chat_layout.remove_widget(self.chat_layout.children[0])

        analysis = report.get("analysis", {})

        # 汇总风险等级
        risk_levels = []
        for name, result in analysis.items():
            level = result.get("risk_level") or result.get("severity") or "UNKNOWN"
            risk_levels.append(level)

        if "HIGH" in risk_levels:
            overall = "HIGH"
            overall_color = C_DANGER
            overall_text = "高风险"
        elif "MEDIUM" in risk_levels:
            overall = "MEDIUM"
            overall_color = C_WARN
            overall_text = "中等风险"
        else:
            overall = "LOW"
            overall_color = C_SAFE
            overall_text = "低风险"

        # 构建审计结果文本
        lines = [f"[b]审计完成[/b]\n\n[b]综合风险等级: {overall_text}[/b]\n"]

        for plugin_name, result in analysis.items():
            lines.append(f"\n[b]▸ {plugin_name}[/b]")
            score = result.get("score", "N/A")
            level = result.get("risk_level") or result.get("severity") or "N/A"
            lines.append(f"  评分: {score}/100  |  等级: {level}")

            if result.get("issues"):
                lines.append("  问题:")
                for issue in result["issues"]:
                    lines.append(f"   - {issue}")
            if result.get("suggestions"):
                lines.append("  建议:")
                for sug in result["suggestions"]:
                    lines.append(f"   - {sug}")
            if result.get("biases"):
                lines.append("  检测到的偏差:")
                for b in result["biases"]:
                    lines.append(f"   - {b['bias']}: {b['evidence']}")
                    lines.append(f"     修正: {b['fix']}")
            if result.get("risks"):
                lines.append("  安全风险:")
                for r in result["risks"]:
                    lines.append(f"   - {r['type']}: {r['detail']}")

        self.add_bubble('\n'.join(lines), is_user=False)

    def _on_audit_error(self, error):
        if self.chat_layout.children:
            self.chat_layout.remove_widget(self.chat_layout.children[0])
        self.add_bubble(f'审计失败: {error}', is_user=False)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size


# =============================================================================
#  App 主类
# =============================================================================

class GCAEApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model_name = "OpenAI (GPT-4o)"
        self.api_key = ""
        self.custom_url = ""

    def build(self):
        sm = ScreenManager()
        sm.add_widget(SetupScreen(name='setup'))
        sm.add_widget(ChatScreen(name='chat'))
        return sm

    def on_start(self):
        self.title = 'GCAE'


if __name__ == '__main__':
    GCAEApp().run()
