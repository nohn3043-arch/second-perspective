# main.py
import uuid
import json
from dataclasses import dataclass
from typing import Dict, Any, List, Callable
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

# ==============================
# 原 Cognitive Audit Engine 核心逻辑
# ==============================
@dataclass
class ResponsibilityAccount:
    organization: str
    role: str
    stage: str
    nonce: str = None

    def __post_init__(self) -> None:
        if not self.nonce:
            self.nonce = uuid.uuid4().hex[:8]

class AuditConfigLoader:
    @staticmethod
    def load_from_dict(config: Dict[str, Any]) -> Dict[str, Any]:
        return config

    @staticmethod
    def load_from_json(path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

class AuditPlugin:
    def __init__(self, name: str, analyze_func: Callable[[Dict[str, Any]], Any]):
        self.name = name
        self.analyze = analyze_func

class CognitiveAuditEngine:
    def __init__(self, account: ResponsibilityAccount, config: Dict[str, Any]):
        self.account = account
        self.config = config
        self.plugins: List[AuditPlugin] = []
        
        allowed_stages = self.config.get("allowed_stages", [])
        if account.stage not in allowed_stages:
            raise ValueError(f"Unsupported stage: {account.stage}")

    def register_plugin(self, plugin: AuditPlugin) -> None:
        self.plugins.append(plugin)

    def audit(self, decision_context: Dict[str, Any]) -> Dict[str, Any]:
        report = {
            "disclaimer": self.config.get("disclaimer", ""),
            "responsibility_account": self.account.__dict__,
            "analysis": {},
            "custom_fields": self.config.get("custom_fields", {})
        }
        for plugin in self.plugins:
            report["analysis"][plugin.name] = plugin.analyze(decision_context)
        return report

# ==============================
# Kivy GUI 界面逻辑
# ==============================
class AuditApp(App):
    def build(self):
        # 主布局：垂直方向
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # 标题
        title = Label(
            text="Cognitive Audit Engine\n(SPL V7.2)",
            font_size=24,
            halign="center",
            valign="middle",
            size_hint=(1, 0.15)
        )
        self.layout.add_widget(title)
        
        # 输入框：用于输入决策上下文
        self.context_input = TextInput(
            hint_text="请输入决策上下文 JSON（例如：{\"user_id\": \"123\", \"action\": \"approve\"}）",
            size_hint=(1, 0.4),
            font_size=14
        )
        self.layout.add_widget(self.context_input)
        
        # 结果展示区域
        self.result_scroll = ScrollView(size_hint=(1, 0.35))
        self.result_label = Label(
            text="审计结果将显示在这里...",
            font_size=12,
            halign="left",
            valign="top",
            size_hint_y=None,
            text_size=(self.layout.width, None)
        )
        self.result_label.bind(
            width=lambda *x: setattr(self.result_label, 'text_size', (self.result_scroll.width, None)),
            texture_size=lambda *x: setattr(self.result_label, 'height', self.result_label.texture_size[1])
        )
        self.result_scroll.add_widget(self.result_label)
        self.layout.add_widget(self.result_scroll)
        
        # 启动审计按钮
        self.start_btn = Button(
            text="执行审计",
            size_hint=(1, 0.1),
            font_size=18,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.start_btn.bind(on_press=self.run_audit)
        self.layout.add_widget(self.start_btn)
        
        return self.layout

    def run_audit(self, instance):
        try:
            # 1. 解析输入的决策上下文
            context_input = self.context_input.text.strip()
            if not context_input:
                self.result_label.text = "❌ 请输入决策上下文"
                return
            decision_context = json.loads(context_input)
            
            # 2. 初始化审计引擎（示例配置）
            account = ResponsibilityAccount(
                organization="NOHN AI TECHNOLOGY",
                role="Auditor",
                stage="production"
            )
            config = AuditConfigLoader.load_from_dict({
                "allowed_stages": ["production", "staging"],
                "disclaimer": "本审计结果仅为技术参考，不构成法律责任依据",
                "custom_fields": {"version": "SPL V7.2"}
            })
            engine = CognitiveAuditEngine(account, config)
            
            # 3. 注册示例插件（可替换为真实业务插件）
            def sample_plugin(context: Dict[str, Any]) -> str:
                return f"✅ 上下文验证通过，包含 {len(context)} 个字段"
            engine.register_plugin(AuditPlugin("ContextValidator", sample_plugin))
            
            # 4. 执行审计并展示结果
            report = engine.audit(decision_context)
            self.result_label.text = json.dumps(report, ensure_ascii=False, indent=2)
            
        except json.JSONDecodeError:
            self.result_label.text = "❌ 输入不是有效的 JSON 格式"
        except Exception as e:
            self.result_label.text = f"❌ 审计执行失败：{str(e)}"

if __name__ == "__main__":
    AuditApp().run()
