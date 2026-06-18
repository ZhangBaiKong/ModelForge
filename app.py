#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型整合 GUI (ModelForge GUI) v0.0.1.1-betaA
更新：Markdown渲染、复制按钮、停止生成、模型方向预设+提示词模板、AI左用户右布局
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import re
import threading
from datetime import datetime

from config_manager import ConfigManager
from engine import Orchestrator

try:
    from updater import Updater
    HAS_UPDATER = True
except ImportError:
    HAS_UPDATER = False


# ================================================================
# 主题配色
# ================================================================
THEMES = {
    "dark": {
        "bg": "#1a1a2e", "surface": "#16213e", "surface2": "#0f3460",
        "accent": "#e94560", "text": "#eaeaea", "muted": "#7f8c8d",
        "entry_bg": "#16213e", "entry_fg": "#eaeaea",
        "btn_bg": "#e94560", "btn_fg": "#ffffff",
        "list_bg": "#16213e", "list_fg": "#eaeaea", "list_sel": "#0f3460",
        "chat_user": "#7aa2f7", "chat_ai": "#9ece6a",
        "user_bubble_bg": "#1e3a5f", "ai_bubble_bg": "#1a2a1a",
        "code_bg": "#0d1117", "inline_code_bg": "#2d333b",
    },
    "light": {
        "bg": "#f0f0f0", "surface": "#ffffff", "surface2": "#e8e8e8",
        "accent": "#2563eb", "text": "#1f2937", "muted": "#9ca3af",
        "entry_bg": "#ffffff", "entry_fg": "#1f2937",
        "btn_bg": "#2563eb", "btn_fg": "#ffffff",
        "list_bg": "#ffffff", "list_fg": "#1f2937", "list_sel": "#dbeafe",
        "chat_user": "#2563eb", "chat_ai": "#16a34a",
        "user_bubble_bg": "#dbeafe", "ai_bubble_bg": "#f0fdf4",
        "code_bg": "#f6f8fa", "inline_code_bg": "#eff1f3",
    },
}


# ================================================================
# 模型方向预设 + 提示词模板
# ================================================================
DIRECTION_PRESETS = {
    "任务调度": {
        "default_prompt": (
            "你是一个任务调度AI。用户会给你文字和可能的图片。\n"
            "你的任务是分析用户需求，决定哪些自己做，哪些分配给其他模型。\n"
            "你擅长：理解需求、分析任务、输出结构化指令。\n"
            "当需要其他模型协助时，输出JSON格式的调度指令。能独立完成的直接回答。"
        ),
    },
    "文本对话": {
        "default_prompt": (
            "你是一个有帮助的AI助手，擅长对话交流、回答问题、提供建议。\n"
            "回答要准确、清晰、有条理。"
        ),
    },
    "代码生成": {
        "default_prompt": (
            "你是一个专业的编程助手。擅长编写、调试和优化代码。\n"
            "回答时：\n1. 先理解需求\n2. 给出完整可运行的代码\n"
            "3. 加上必要的注释\n4. 解释关键逻辑"
        ),
    },
    "图片识别": {
        "default_prompt": (
            "你是一个图像分析专家。能详细描述图片中的内容，\n"
            "包括文字、布局、颜色、物体、风格等。\n"
            "请用结构化的方式描述，便于其他AI进行后续处理。"
        ),
    },
    "界面生成": {
        "default_prompt": (
            "你是一个前端界面设计专家。能根据描述生成网页界面代码（HTML/CSS）。\n"
            "要求：\n1. 代码完整可运行\n2. 界面美观现代\n"
            "3. 响应式布局\n4. 添加必要的注释"
        ),
    },
    "翻译": {
        "default_prompt": (
            "你是一个专业翻译。能准确翻译各种语言，保持原文的语义、风格和语气。\n"
            "翻译时注意：\n1. 专业术语的准确性\n2. 语境的自然流畅\n3. 文化差异的处理"
        ),
    },
    "数据分析": {
        "default_prompt": (
            "你是一个数据分析专家。能分析数据、发现规律、生成报告。\n"
            "回答时用表格、列表等结构化方式呈现结果。"
        ),
    },
    "写作助手": {
        "default_prompt": (
            "你是一个写作助手。擅长各种文体的写作，包括文章、邮件、文案、报告等。\n"
            "写作时注意：\n1. 结构清晰\n2. 语言得体\n3. 符合目标读者\n4. 逻辑连贯"
        ),
    },
    "自定义": {
        "default_prompt": "",
    },
}


# ================================================================
# 多语言
# ================================================================
LANG = {
    "zh": {
        "title": "模型整合 (ModelForge) v0.0.1.1-beta",
        "new_chat": "＋ 新建对话",
        "search_hint": "搜索对话...",
        "pin": "置顶", "unpin": "取消置顶",
        "rename": "重命名", "delete": "删除", "export": "导出",
        "models": "模型 (Models)",
        "add_model": "＋ 添加模型",
        "main": "主模型", "sub": "副模型",
        "logs": "运行日志 (Logs)",
        "settings": "软件设置 (Settings)",
        "theme": "主题 (Theme)",
        "dark": "深色 Dark", "light": "浅色 Light",
        "lang": "语言 (Language)",
        "storage": "存储路径 (Storage)",
        "browse": "浏览",
        "send": "发送", "stop": "停止",
        "copy": "复制",
        "cfg_model": "配置模型 (Model Config)",
        "m_name": "名称 (Name)",
        "m_role": "角色 (Role)",
        "m_dir": "方向 (Direction)",
        "m_url": "API 地址 (API URL)",
        "m_key": "API 密钥 (API Key)",
        "m_id": "模型名 (Model ID)",
        "m_temp": "温度 (Temperature)",
        "m_tokens": "最大 Token (Max Tokens)",
        "m_prompt": "系统提示词 (System Prompt)",
        "m_prompt_hint": "选择方向后自动填充，可自行修改",
        "test": "测试连接 (Test)",
        "save": "保存", "cancel": "取消",
        "thinking": "思考中...",
        "welcome": "欢迎使用模型整合 (ModelForge)！\n请先在右侧配置主模型。",
        "del_confirm": "确认删除此对话？",
        "del_model_confirm": "确认删除此模型？",
        "dirs": list(DIRECTION_PRESETS.keys()),
    },
    "en": {
        "title": "ModelForge v0.0.1.1-beta",
        "new_chat": "+ New Chat",
        "search_hint": "Search...",
        "pin": "Pin", "unpin": "Unpin",
        "rename": "Rename", "delete": "Delete", "export": "Export",
        "models": "Models",
        "add_model": "+ Add Model",
        "main": "Main", "sub": "Sub",
        "logs": "Logs",
        "settings": "Settings",
        "theme": "Theme",
        "dark": "Dark", "light": "Light",
        "lang": "Language",
        "storage": "Storage",
        "browse": "Browse",
        "send": "Send", "stop": "Stop",
        "copy": "Copy",
        "cfg_model": "Model Config",
        "m_name": "Name", "m_role": "Role",
        "m_dir": "Direction", "m_url": "API URL", "m_key": "API Key",
        "m_id": "Model ID", "m_temp": "Temperature",
        "m_tokens": "Max Tokens", "m_prompt": "System Prompt",
        "m_prompt_hint": "Auto-filled when direction is selected",
        "test": "Test Connection", "save": "Save", "cancel": "Cancel",
        "thinking": "Thinking...",
        "welcome": "Welcome to ModelForge!\nPlease configure the main model first.",
        "del_confirm": "Delete this conversation?",
        "del_model_confirm": "Delete this model?",
        "dirs": list(DIRECTION_PRESETS.keys()),
    },
}


# ================================================================
# 模型配置弹窗（重构版：含角色选择+方向预设+提示词模板）
# ================================================================
class ModelConfigDialog(tk.Toplevel):
    def __init__(self, parent, theme, lang, model_data=None, callback=None):
        super().__init__(parent)
        self.theme = theme
        self.lang = lang
        self.model_data = model_data or {}
        self.callback = callback
        self._show_key = False
        self.direction_vars = {}  # 多选用字典

        self.title(lang["cfg_model"])
        # 适配屏幕大小
        sh = parent.winfo_screenheight()
        h = min(700, sh - 80)
        self.geometry(f"520x{h}")
        self.configure(bg=theme["bg"])
        self.resizable(False, False)
        self.grab_set()

        self._build()
        if model_data:
            self._load(model_data)

    def _lbl(self, parent, text):
        tk.Label(
            parent, text=text, bg=self.theme["bg"], fg=self.theme["muted"],
            font=("Microsoft YaHei", 9), anchor="w",
        ).pack(fill="x", pady=(8, 2))

    def _entry(self, parent):
        e = tk.Entry(
            parent, bg=self.theme["entry_bg"], fg=self.theme["entry_fg"],
            insertbackground=self.theme["text"], relief="flat",
            font=("Consolas", 10),
        )
        e.pack(fill="x", pady=(0, 4))
        return e

    def _build(self):
        t, l = self.theme, self.lang

        # 可滚动容器
        canvas = tk.Canvas(self, bg=t["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=t["bg"])

        scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", tags="inner")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 让内容宽度跟canvas一致
        def _resize_inner(event):
            canvas.itemconfig("inner", width=event.width - 4)
        canvas.bind("<Configure>", _resize_inner)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        pad = tk.Frame(scroll_frame, bg=t["bg"], padx=20, pady=10)
        pad.pack(fill="both", expand=True)

        # ── 名称 ──
        self._lbl(pad, l["m_name"])
        self.w_name = self._entry(pad)

        # ── 角色 ──
        self._lbl(pad, l["m_role"])
        role_frame = tk.Frame(pad, bg=t["bg"])
        role_frame.pack(fill="x", pady=(0, 4))
        self.role_var = tk.StringVar(value="sub")
        tk.Radiobutton(
            role_frame, text=f"⭐ {l['main']}", variable=self.role_var,
            value="main", bg=t["bg"], fg=t["chat_user"],
            selectcolor=t["surface2"], activebackground=t["bg"],
            font=("Microsoft YaHei", 9)
        ).pack(side="left", padx=(0, 20))
        tk.Radiobutton(
            role_frame, text=f"🔧 {l['sub']}", variable=self.role_var,
            value="sub", bg=t["bg"], fg=t["chat_ai"],
            selectcolor=t["surface2"], activebackground=t["bg"],
            font=("Microsoft YaHei", 9)
        ).pack(side="left")

        # ── 方向（多选） ──
        self._lbl(pad, "方向 (支持多选)")
        dir_frame = tk.Frame(pad, bg=t["surface"], bd=1, relief="groove")
        dir_frame.pack(fill="x", pady=(0, 4))

        # 两列排列
        dirs = list(DIRECTION_PRESETS.keys())
        col = 0
        row = 0
        for d in dirs:
            var = tk.BooleanVar(value=False)
            self.direction_vars[d] = var
            cb = tk.Checkbutton(
                dir_frame, text=d, variable=var,
                bg=t["surface"], fg=t["text"], selectcolor=t["surface2"],
                activebackground=t["surface"], activeforeground=t["text"],
                font=("Microsoft YaHei", 9),
                command=self._on_direction_change,
            )
            cb.grid(row=row, column=col, sticky="w", padx=8, pady=1)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        # ── API地址 ──
        self._lbl(pad, l["m_url"])
        self.w_url = self._entry(pad)

        # ── API密钥 ──
        self._lbl(pad, l["m_key"])
        key_frame = tk.Frame(pad, bg=t["bg"])
        key_frame.pack(fill="x", pady=(0, 4))
        self.w_key = tk.Entry(
            key_frame, show="*", bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat", font=("Consolas", 10),
        )
        self.w_key.pack(side="left", fill="x", expand=True)
        tk.Button(
            key_frame, text="👁", command=self._toggle_key,
            bg=t["surface"], fg=t["text"], relief="flat", width=3,
        ).pack(side="right", padx=(4, 0))

        # ── 模型名 ──
        self._lbl(pad, l["m_id"])
        self.w_model = self._entry(pad)

        # ── 温度 ──
        self._lbl(pad, l["m_temp"])
        self.w_temp = tk.Scale(
            pad, from_=0, to=2, resolution=0.1, orient="horizontal",
            bg=t["bg"], fg=t["text"], highlightthickness=0,
            troughcolor=t["surface2"], activebackground=t["accent"],
        )
        self.w_temp.set(0.7)
        self.w_temp.pack(fill="x", pady=(0, 4))

        # ── 最大Token ──
        self._lbl(pad, l["m_tokens"])
        self.w_tokens = self._entry(pad)
        self.w_tokens.insert(0, "4096")

        # ── 系统提示词 ──
        self._lbl(pad, l["m_prompt"])
        tk.Label(
            pad, text="多选方向时自动合并提示词，可自行修改",
            bg=t["bg"], fg=t["muted"], font=("Microsoft YaHei", 8), anchor="w"
        ).pack(fill="x", pady=(0, 2))
        self.w_prompt = tk.Text(
            pad, height=5, bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat",
            font=("Consolas", 9), wrap="word",
        )
        self.w_prompt.pack(fill="x", pady=(0, 10))

        # ── 按钮 ──
        btn_frame = tk.Frame(pad, bg=t["bg"])
        btn_frame.pack(fill="x")
        tk.Button(
            btn_frame, text=l["test"], command=self._test_connection,
            bg=t["surface2"], fg=t["text"], relief="flat", padx=12,
        ).pack(side="left")
        tk.Button(
            btn_frame, text=l["save"], command=self._save,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat", padx=16,
        ).pack(side="right", padx=(4, 0))
        tk.Button(
            btn_frame, text=l["cancel"], command=self.destroy,
            bg=t["surface"], fg=t["text"], relief="flat", padx=12,
        ).pack(side="right")

    def _on_direction_change(self):
        """方向多选变化时，合并提示词"""
        selected = [d for d, v in self.direction_vars.items() if v.get()]
        if not selected:
            return

        current = self.w_prompt.get("1.0", "end").strip()
        # 如果当前为空或正好是旧的自动填充内容，直接替换
        merged_parts = []
        for d in selected:
            preset = DIRECTION_PRESETS.get(d, {})
            prompt = preset.get("default_prompt", "")
            if prompt:
                merged_parts.append(f"【{d}】\n{prompt}")

        if merged_parts:
            new_prompt = "\n\n".join(merged_parts)
            if not current or messagebox.askyesno(
                    "提示", "是否用选中方向的提示词替换当前内容？"):
                self.w_prompt.delete("1.0", "end")
                self.w_prompt.insert("1.0", new_prompt)

    def _toggle_key(self):
        self._show_key = not self._show_key
        self.w_key.config(show="" if self._show_key else "*")

    def _load(self, d):
        self.w_name.insert(0, d.get("name", ""))
        self.role_var.set(d.get("role", "sub"))

        # 多选方向回填
        direction_str = d.get("direction", "")
        selected_dirs = [x.strip() for x in direction_str.split("+") if x.strip()]
        for dirname, var in self.direction_vars.items():
            var.set(dirname in selected_dirs)

        self.w_url.insert(0, d.get("api_url", ""))
        self.w_key.insert(0, d.get("api_key", ""))
        self.w_model.insert(0, d.get("model_name", ""))
        self.w_temp.set(d.get("temperature", 0.7))
        self.w_tokens.delete(0, "end")
        self.w_tokens.insert(0, str(d.get("max_tokens", 4096)))
        self.w_prompt.insert("1.0", d.get("system_prompt", ""))

    def _get_data(self):
        selected = [d for d, v in self.direction_vars.items() if v.get()]
        return {
            "name": self.w_name.get().strip(),
            "role": self.role_var.get(),
            "direction": " + ".join(selected),
            "api_url": self.w_url.get().strip(),
            "api_key": self.w_key.get().strip(),
            "model_name": self.w_model.get().strip(),
            "temperature": self.w_temp.get(),
            "max_tokens": int(self.w_tokens.get() or 4096),
            "system_prompt": self.w_prompt.get("1.0", "end").strip(),
        }

    def _test_connection(self):
        import requests as rq
        d = self._get_data()
        if not d["api_url"] or not d["api_key"]:
            messagebox.showwarning("提示", "请填写 API 地址和密钥")
            return

        def go():
            try:
                h = {"Content-Type": "application/json",
                     "Authorization": f"Bearer {d['api_key']}"}
                p = {"model": d["model_name"],
                     "messages": [{"role": "user", "content": "hi"}],
                     "max_tokens": 5}
                r = rq.post(d["api_url"], headers=h, json=p, timeout=15)
                r.raise_for_status()
                self.after(0, lambda: messagebox.showinfo("成功", "连接正常！"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("失败", str(e)))

        threading.Thread(target=go, daemon=True).start()

    def _save(self):
        d = self._get_data()
        if not d["name"]:
            messagebox.showwarning("提示", "请填写模型名称")
            return
        if not d["direction"]:
            messagebox.showwarning("提示", "请至少选择一个方向")
            return
        if self.callback:
            self.callback(d)
        self.destroy()


# ================================================================
# 主应用
# ================================================================
class ModelForgeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.cfg = ConfigManager()
        self.orch = Orchestrator(self.cfg, log_callback=self.add_log)

        theme_name = self.cfg.get("theme", "dark")
        lang_code = self.cfg.get("language", "zh")
        self.t = THEMES.get(theme_name, THEMES["dark"])
        self.l = LANG.get(lang_code, LANG["zh"])

        self.conv_id_list = []
        self.conversations = {}
        self.current_conv = None
        self.attachments = []
        self._is_generating = False
        self._last_ai_response = ""

        if HAS_UPDATER:
            self.updater = Updater(log_callback=self.add_log)

        self._setup_window()
        self._create_left_panel()
        self._create_center_panel()
        self._create_right_panel()
        self._load_all_conversations()
        self._refresh_model_list()
        self.add_log("应用已启动 v0.0.1.1-beta")

        if HAS_UPDATER:
            self.root.after(5000, self._auto_check_update)

    # ────────────────────────────────────────
    # 窗口
    # ────────────────────────────────────────
    def _setup_window(self):
        self.root.title(self.l["title"])
        self.root.geometry("1200x720")
        self.root.minsize(900, 550)
        self.root.configure(bg=self.t["bg"])
        self.root.columnconfigure(0, weight=1, minsize=180)
        self.root.columnconfigure(1, weight=3, minsize=350)
        self.root.columnconfigure(2, weight=2, minsize=260)
        self.root.rowconfigure(0, weight=1)
        self.root.update_idletasks()
        w, h = 1200, 720
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ────────────────────────────────────────
    # 左栏：对话列表
    # ────────────────────────────────────────
    def _create_left_panel(self):
        t, l = self.t, self.l
        panel = tk.Frame(self.root, bg=t["bg"])
        panel.grid(row=0, column=0, sticky="nsew", padx=(5, 2), pady=5)
        panel.rowconfigure(2, weight=1)
        panel.columnconfigure(0, weight=1)

        tk.Label(
            panel, text=l["title"], bg=t["bg"], fg=t["accent"],
            font=("Microsoft YaHei", 12, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(5, 8))

        tk.Button(
            panel, text=l["new_chat"], command=self._new_conv,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat",
            font=("Microsoft YaHei", 9),
        ).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))

        search_frame = tk.Frame(panel, bg=t["bg"])
        search_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(32, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_conv_list())
        se = tk.Entry(
            search_frame, textvariable=self.search_var,
            bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat",
            font=("Microsoft YaHei", 9),
        )
        se.pack(fill="x")
        hint = l["search_hint"]
        se.insert(0, hint)
        se.bind("<FocusIn>", lambda e: se.delete(0, "end") if se.get() == hint else None)

        self.conv_lb = tk.Listbox(
            panel, bg=t["list_bg"], fg=t["list_fg"],
            selectbackground=t["list_sel"], selectforeground=t["list_fg"],
            relief="flat", font=("Microsoft YaHei", 10),
            activestyle="none", highlightthickness=0,
        )
        self.conv_lb.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        self.conv_lb.bind("<<ListboxSelect>>", self._on_conv_select)
        self.conv_lb.bind("<Button-3>", self._conv_context_menu)

        sb = tk.Scrollbar(panel, command=self.conv_lb.yview)
        sb.grid(row=2, column=1, sticky="ns")
        self.conv_lb.config(yscrollcommand=sb.set)

    # ────────────────────────────────────────
    # 中栏：对话区
    # ────────────────────────────────────────
    def _create_center_panel(self):
        t, l = self.t, self.l
        panel = tk.Frame(self.root, bg=t["bg"])
        panel.grid(row=0, column=1, sticky="nsew", padx=2, pady=5)
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        self.chat_text = tk.Text(
            panel, bg=t["surface"], fg=t["text"], relief="flat",
            font=("Microsoft YaHei", 10), wrap="word", state="disabled",
            insertbackground=t["text"], highlightthickness=0, padx=12, pady=8,
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        csb = tk.Scrollbar(panel, command=self.chat_text.yview)
        csb.grid(row=0, column=1, sticky="ns")
        self.chat_text.config(yscrollcommand=csb.set)

        # ── 消息标签 ──
        # 用户消息（右对齐）
        self.chat_text.tag_configure(
            "user_header", justify="right", foreground=t["chat_user"],
            font=("Microsoft YaHei", 9, "bold"),
            rmargin=10, lmargin1=200)
        self.chat_text.tag_configure(
            "user_bubble", justify="right",
            foreground=t["text"], background=t["user_bubble_bg"],
            font=("Microsoft YaHei", 10),
            rmargin=10, lmargin1=200,
            spacing1=2, spacing3=8,
            )
        self.chat_text.tag_configure(
            "file_tag_right", justify="right", foreground="#e0a030",
            font=("Microsoft YaHei", 9, "italic"),
            rmargin=10, lmargin1=200)

        # AI消息（左对齐）
        self.chat_text.tag_configure(
            "ai_header", justify="left", foreground=t["chat_ai"],
            font=("Microsoft YaHei", 9, "bold"),
            lmargin1=10, rmargin=200)
        self.chat_text.tag_configure(
            "ai_bubble", justify="left",
            foreground=t["text"],
            font=("Microsoft YaHei", 10),
            lmargin1=10, rmargin=200,
            spacing1=2, spacing3=8)

        # Markdown标签
        self.chat_text.tag_configure(
            "md_h1", font=("Microsoft YaHei", 14, "bold"),
            foreground=t["accent"], spacing1=8, spacing3=4)
        self.chat_text.tag_configure(
            "md_h2", font=("Microsoft YaHei", 12, "bold"),
            foreground=t["chat_user"], spacing1=6, spacing3=4)
        self.chat_text.tag_configure(
            "md_h3", font=("Microsoft YaHei", 11, "bold"),
            foreground=t["text"], spacing1=4, spacing3=2)
        self.chat_text.tag_configure(
            "md_bold", font=("Microsoft YaHei", 10, "bold"))
        self.chat_text.tag_configure(
            "md_italic", font=("Microsoft YaHei", 10, "italic"))
        self.chat_text.tag_configure(
            "md_inline_code", font=("Consolas", 9),
            background=t["inline_code_bg"], foreground="#e06c75")
        self.chat_text.tag_configure(
            "md_code_block", font=("Consolas", 9),
            background=t["code_bg"], foreground="#abb2bf",
            lmargin1=20, rmargin=20,
            spacing1=4, spacing3=4, relief="flat")
        self.chat_text.tag_configure(
            "md_list", lmargin1=30, rmargin=10)

        # 系统消息
        self.chat_text.tag_configure(
            "sys", foreground=t["muted"],
            font=("Microsoft YaHei", 9, "italic"), justify="center")
        self.chat_text.tag_configure("thinking_tag", foreground=t["accent"])

        # 附件提示条
        self.attach_bar = tk.Frame(panel, bg=t["surface2"], height=28)
        self.attach_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.attach_bar.grid_propagate(False)
        self.attach_label = tk.Label(
            self.attach_bar, text="", bg=t["surface2"], fg="#e0a030",
            font=("Microsoft YaHei", 9), anchor="w", padx=8)
        self.attach_label.pack(side="left", fill="x", expand=True)
        self.attach_clear_btn = tk.Button(
            self.attach_bar, text="✕ 清除", command=self._clear_attachments,
            bg=t["surface2"], fg="#e0a030", relief="flat",
            font=("Microsoft YaHei", 8))
        self.attach_clear_btn.pack(side="right", padx=8)
        self.attach_bar.grid_remove()

        # 输入区
        inp = tk.Frame(panel, bg=t["bg"])
        inp.grid(row=2, column=0, columnspan=2, sticky="ew")
        inp.columnconfigure(1, weight=1)

        tk.Button(
            inp, text="📎", command=self._attach_file,
            bg=t["surface2"], fg=t["text"], relief="flat", width=3,
        ).grid(row=0, column=0, padx=(0, 4))

        tk.Button(
            inp, text=l["copy"], command=self._copy_last_response,
            bg=t["surface2"], fg=t["text"], relief="flat",
            font=("Microsoft YaHei", 8),
        ).grid(row=0, column=0, padx=(30, 4), sticky="w")

        self.input_text = tk.Text(
            inp, bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat",
            font=("Microsoft YaHei", 10), height=3, wrap="word",
            highlightthickness=0,
        )
        self.input_text.grid(row=0, column=1, sticky="ew")
        self.input_text.bind("<Control-Return>", lambda e: self._send())

        self.send_btn = tk.Button(
            inp, text=l["send"], command=self._send,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat", padx=16,
            font=("Microsoft YaHei", 10, "bold"),
        )
        self.send_btn.grid(row=0, column=2, padx=(4, 0))

        self._show_welcome()

    # ────────────────────────────────────────
    # 右栏
    # ────────────────────────────────────────
    def _create_right_panel(self):
        t, l = self.t, self.l
        panel = tk.Frame(self.root, bg=t["bg"])
        panel.grid(row=0, column=2, sticky="nsew", padx=(2, 5), pady=5)
        panel.rowconfigure(0, weight=2)
        panel.rowconfigure(1, weight=3)
        panel.rowconfigure(2, weight=0)
        panel.columnconfigure(0, weight=1)

        # 模型面板
        mf = tk.LabelFrame(
            panel, text=f" {l['models']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        mf.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
        mf.rowconfigure(0, weight=1)
        mf.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Model.Treeview", background=t["surface"],
                        foreground=t["text"], fieldbackground=t["surface"],
                        rowheight=26, font=("Microsoft YaHei", 9))
        style.configure("Model.Treeview.Heading", background=t["surface2"],
                        foreground=t["muted"], font=("Microsoft YaHei", 9))

        self.model_tree = ttk.Treeview(
            mf, style="Model.Treeview", columns=("role", "dir"),
            show="tree headings", height=5)
        self.model_tree.heading("#0", text=l["m_name"])
        self.model_tree.heading("role", text=l["m_role"])
        self.model_tree.heading("dir", text=l["m_dir"])
        self.model_tree.column("#0", width=90)
        self.model_tree.column("role", width=50)
        self.model_tree.column("dir", width=90)
        self.model_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.model_tree.bind("<Double-1>", self._edit_model)
        self.model_tree.bind("<Button-3>", self._model_context_menu)

        tk.Button(
            mf, text=l["add_model"], command=self._add_model,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat",
            font=("Microsoft YaHei", 9),
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        # 日志面板
        lf = tk.LabelFrame(
            panel, text=f" {l['logs']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        lf.grid(row=1, column=0, sticky="nsew", pady=3)
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            lf, bg=t["surface"], fg=t["muted"], relief="flat",
            font=("Consolas", 9), wrap="word", state="disabled",
            highlightthickness=0, padx=6, pady=4)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        lsb = tk.Scrollbar(lf, command=self.log_text.yview)
        lsb.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=lsb.set)

        # 设置面板
        sf = tk.LabelFrame(
            panel, text=f" {l['settings']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        sf.grid(row=2, column=0, sticky="ew", pady=(3, 0))

        r1 = tk.Frame(sf, bg=t["surface"])
        r1.pack(fill="x", padx=8, pady=2)
        tk.Label(r1, text=l["theme"], bg=t["surface"], fg=t["text"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.theme_cb = ttk.Combobox(
            r1, values=[l["dark"], l["light"]], state="readonly", width=10)
        self.theme_cb.set(l["dark"] if self.cfg.get("theme") == "dark" else l["light"])
        self.theme_cb.pack(side="right")
        self.theme_cb.bind("<<ComboboxSelected>>", self._change_theme)

        r2 = tk.Frame(sf, bg=t["surface"])
        r2.pack(fill="x", padx=8, pady=2)
        tk.Label(r2, text=l["lang"], bg=t["surface"], fg=t["text"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.lang_cb = ttk.Combobox(
            r2, values=["中文", "English"], state="readonly", width=10)
        self.lang_cb.set("中文" if self.cfg.get("language") == "zh" else "English")
        self.lang_cb.pack(side="right")
        self.lang_cb.bind("<<ComboboxSelected>>", self._change_lang)

        r3 = tk.Frame(sf, bg=t["surface"])
        r3.pack(fill="x", padx=8, pady=2)
        tk.Label(r3, text=l["storage"], bg=t["surface"], fg=t["text"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        tk.Button(r3, text=l["browse"], command=self._browse_storage,
                  bg=t["surface2"], fg=t["text"], relief="flat").pack(side="right")

        if HAS_UPDATER:
            r4 = tk.Frame(sf, bg=t["surface"])
            r4.pack(fill="x", padx=8, pady=(2, 6))
            tk.Button(r4, text="检查更新 (Check Update)",
                      command=self._manual_check_update,
                      bg=t["surface2"], fg=t["text"], relief="flat").pack(fill="x")

    # ================================================================
    # Markdown 渲染
    # ================================================================
    def _render_markdown(self, text):
        """将Markdown文本渲染到chat_text控件中"""
        lines = text.split('\n')
        in_code_block = False
        code_lines = []

        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    code_text = '\n'.join(code_lines)
                    self.chat_text.insert("end", code_text + "\n", "md_code_block")
                    code_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            if line.startswith('### '):
                self.chat_text.insert("end", line[4:] + "\n", "md_h3")
            elif line.startswith('## '):
                self.chat_text.insert("end", line[3:] + "\n", "md_h2")
            elif line.startswith('# '):
                self.chat_text.insert("end", line[2:] + "\n", "md_h1")
            elif re.match(r'^[-*]\s', line):
                self.chat_text.insert("end", "  • ", "md_list")
                self._render_inline(re.sub(r'^[-*]\s', '', line) + "\n", "md_list")
            elif re.match(r'^\d+\.\s', line):
                m = re.match(r'^(\d+\.\s)(.*)', line)
                self.chat_text.insert("end", f"  {m.group(1)}", "md_list")
                self._render_inline(m.group(2) + "\n", "md_list")
            elif line.strip() == '':
                self.chat_text.insert("end", "\n")
            else:
                self._render_inline(line + "\n", "ai_bubble")

        if in_code_block and code_lines:
            code_text = '\n'.join(code_lines)
            self.chat_text.insert("end", code_text + "\n", "md_code_block")

    def _render_inline(self, text, base_tag="ai_bubble"):
        """渲染行内Markdown：粗体、斜体、行内代码"""
        pattern = r'(\*\*(.+?)\*\*|`([^`]+)`|\*(.+?)\*)'
        last_end = 0
        for m in re.finditer(pattern, text):
            if m.start() > last_end:
                self.chat_text.insert("end", text[last_end:m.start()], base_tag)
            if m.group(2):
                self.chat_text.insert("end", m.group(2), "md_bold")
            elif m.group(3):
                self.chat_text.insert("end", m.group(3), "md_inline_code")
            elif m.group(4):
                self.chat_text.insert("end", m.group(4), "md_italic")
            last_end = m.end()
        if last_end < len(text):
            self.chat_text.insert("end", text[last_end:], base_tag)

    # ================================================================
    # 对话管理
    # ================================================================
    def _load_all_conversations(self):
        sp = self.cfg.get("storage_path", "./conversations")
        os.makedirs(sp, exist_ok=True)
        self.conversations = {}
        for fn in os.listdir(sp):
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(sp, fn), "r", encoding="utf-8") as f:
                        c = json.load(f)
                        self.conversations[c["id"]] = c
                except Exception:
                    pass
        self._refresh_conv_list()

    def _save_conv(self, cid):
        c = self.conversations.get(cid)
        if not c:
            return
        sp = self.cfg.get("storage_path", "./conversations")
        os.makedirs(sp, exist_ok=True)
        with open(os.path.join(sp, f"{cid}.json"), "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=2)

    def _new_conv(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cid = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversations[cid] = {
            "id": cid, "title": "新对话", "created": now, "updated": now,
            "pinned": False, "messages": [],
        }
        self._save_conv(cid)
        self._refresh_conv_list()
        self._switch_conv(cid)

    def _refresh_conv_list(self):
        q = self.search_var.get().strip().lower()
        hint = self.l["search_hint"].lower()
        if q == hint:
            q = ""
        self.conv_lb.delete(0, "end")
        self.conv_id_list = []
        pinned = sorted(
            [c for c in self.conversations.values() if c.get("pinned")],
            key=lambda c: c.get("updated", ""), reverse=True)
        normal = sorted(
            [c for c in self.conversations.values() if not c.get("pinned")],
            key=lambda c: c.get("updated", ""), reverse=True)
        for c in pinned + normal:
            if q and q not in c["title"].lower():
                continue
            prefix = "📌 " if c.get("pinned") else ""
            self.conv_lb.insert("end", f"{prefix}{c['title']}")
            self.conv_id_list.append(c["id"])

    def _on_conv_select(self, event=None):
        sel = self.conv_lb.curselection()
        if not sel:
            return
        self._switch_conv(self.conv_id_list[sel[0]])

    def _switch_conv(self, cid):
        if cid not in self.conversations:
            return
        self.current_conv = cid
        self._render_chat()

    def _render_chat(self):
        self.chat_text.config(state="normal")
        self.chat_text.delete("1.0", "end")
        c = self.conversations.get(self.current_conv)
        if not c:
            self.chat_text.config(state="disabled")
            return

        for msg in c["messages"]:
            ts = msg.get("timestamp", "")[-8:]

            if msg["role"] == "user":
                # 附件信息（右对齐）
                atts = msg.get("attachments", [])
                if atts:
                    self.chat_text.insert(
                        "end", f"📎 {', '.join(atts)}\n", "file_tag_right")
                # 用户消息（右对齐气泡）
                self.chat_text.insert("end", f"{msg['content']}\n", "user_bubble")
                self.chat_text.insert("end", f"你  {ts}\n", "user_header")
            else:
                # AI消息（左对齐）
                self.chat_text.insert("end", f"AI  {ts}\n", "ai_header")
                self._render_markdown(msg["content"])

            self.chat_text.insert("end", "\n")

        self.chat_text.config(state="disabled")
        self.chat_text.see("end")

    def _show_welcome(self):
        self.chat_text.config(state="normal")
        self.chat_text.insert("end", self.l["welcome"] + "\n", "sys")
        self.chat_text.config(state="disabled")

    def _conv_context_menu(self, event):
        idx = self.conv_lb.nearest(event.y)
        if idx < 0:
            return
        self.conv_lb.selection_set(idx)
        cid = self.conv_id_list[idx]
        c = self.conversations.get(cid, {})
        menu = tk.Menu(self.root, tearoff=0, bg=self.t["surface"],
                       fg=self.t["text"], relief="flat")
        if c.get("pinned"):
            menu.add_command(label=self.l["unpin"],
                             command=lambda: self._pin(cid, False))
        else:
            menu.add_command(label=self.l["pin"],
                             command=lambda: self._pin(cid, True))
        menu.add_command(label=self.l["rename"], command=lambda: self._rename(cid))
        menu.add_command(label=self.l["export"], command=lambda: self._export(cid))
        menu.add_separator()
        menu.add_command(label=self.l["delete"], command=lambda: self._delete_conv(cid))
        menu.tk_popup(event.x_root, event.y_root)

    def _pin(self, cid, val):
        self.conversations[cid]["pinned"] = val
        self._save_conv(cid)
        self._refresh_conv_list()

    def _rename(self, cid):
        old = self.conversations[cid]["title"]
        new = simpledialog.askstring(self.l["rename"], self.l["rename"],
                                     initialvalue=old, parent=self.root)
        if new and new.strip():
            self.conversations[cid]["title"] = new.strip()
            self._save_conv(cid)
            self._refresh_conv_list()

    def _export(self, cid):
        c = self.conversations.get(cid)
        if not c:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("JSON", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            if path.endswith(".json"):
                json.dump(c, f, ensure_ascii=False, indent=2)
            else:
                for m in c["messages"]:
                    role = "你" if m["role"] == "user" else "AI"
                    f.write(f"[{role}] {m.get('timestamp','')}\n{m['content']}\n\n")

    def _delete_conv(self, cid):
        if not messagebox.askyesno("", self.l["del_confirm"]):
            return
        sp = self.cfg.get("storage_path", "./conversations")
        fp = os.path.join(sp, f"{cid}.json")
        if os.path.exists(fp):
            os.remove(fp)
        self.conversations.pop(cid, None)
        if self.current_conv == cid:
            self.current_conv = None
            self.chat_text.config(state="normal")
            self.chat_text.delete("1.0", "end")
            self.chat_text.config(state="disabled")
        self._refresh_conv_list()

    # ================================================================
    # 模型管理
    # ================================================================
    def _refresh_model_list(self):
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
        main = self.cfg.get_main_model()
        if main:
            role_text = "⭐ " + self.l["main"]
            self.model_tree.insert(
                "", "end", iid="main", text=main.get("name", "未命名"),
                values=(role_text, main.get("direction", "")))
        for i, sub in enumerate(self.cfg.get_sub_models()):
            role_text = "🔧 " + self.l["sub"]
            self.model_tree.insert(
                "", "end", iid=f"sub_{i}", text=sub.get("name", "未命名"),
                values=(role_text, sub.get("direction", "")))

    def _add_model(self):
        def on_save(data):
            role = data.pop("role", "sub")
            if role == "main":
                existing = self.cfg.get_main_model()
                if existing:
                    if not messagebox.askyesno(
                            "提示", f"已有主模型 [{existing['name']}]，是否替换？"):
                        return
                data["id"] = "main"
                self.cfg.set_main_model(data)
            else:
                data["id"] = f"sub_{len(self.cfg.get_sub_models())}"
                self.cfg.add_sub_model(data)
            self._refresh_model_list()
            self.add_log(f"已添加模型: {data['name']} ({role})")

        ModelConfigDialog(self.root, self.t, self.l, callback=on_save)

    def _edit_model(self, event=None):
        sel = self.model_tree.selection()
        if not sel:
            return
        iid = sel[0]
        if iid == "main":
            data = self.cfg.get_main_model()
            if not data:
                return
            data["role"] = "main"

            def on_save(d):
                d.pop("role", None)
                d["id"] = "main"
                self.cfg.set_main_model(d)
                self._refresh_model_list()
                self.add_log(f"已更新主模型: {d['name']}")
        else:
            idx = int(iid.split("_")[1])
            subs = self.cfg.get_sub_models()
            if idx >= len(subs):
                return
            data = subs[idx]
            data["role"] = "sub"

            def on_save(d):
                d.pop("role", None)
                d["id"] = f"sub_{idx}"
                self.cfg.update_sub_model(idx, d)
                self._refresh_model_list()
                self.add_log(f"已更新副模型: {d['name']}")

        ModelConfigDialog(self.root, self.t, self.l, model_data=data, callback=on_save)

    def _model_context_menu(self, event):
        sel = self.model_tree.selection()
        if not sel:
            return
        iid = sel[0]
        menu = tk.Menu(self.root, tearoff=0, bg=self.t["surface"],
                       fg=self.t["text"], relief="flat")
        menu.add_command(label="编辑 (Edit)", command=self._edit_model)
        menu.add_command(label="删除 (Delete)",
                         command=lambda: self._delete_model(iid))
        menu.tk_popup(event.x_root, event.y_root)

    def _delete_model(self, iid):
        if not messagebox.askyesno("", self.l["del_model_confirm"]):
            return
        if iid == "main":
            self.cfg.set_main_model(None)
        else:
            idx = int(iid.split("_")[1])
            self.cfg.remove_sub_model(idx)
        self._refresh_model_list()
        self.add_log("已删除模型")

    # ================================================================
    # 发送 / 停止
    # ================================================================
    def _send(self):
        if self._is_generating:
            self._stop_generation()
            return

        msg = self.input_text.get("1.0", "end").strip()
        if not msg and not self.attachments:
            return
        self.input_text.delete("1.0", "end")

        if not self.current_conv:
            title = (msg or "图片对话")[:25]
            if len(msg or "图片对话") > 25:
                title += "..."
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cid = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.conversations[cid] = {
                "id": cid, "title": title, "created": now, "updated": now,
                "pinned": False, "messages": [],
            }
            self.current_conv = cid
            self._refresh_conv_list()
            self._switch_conv(cid)

        conv = self.conversations[self.current_conv]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_names = [os.path.basename(p) for p in self.attachments]
        conv["messages"].append({
            "role": "user", "content": msg, "timestamp": now,
            "attachments": file_names,
        })
        conv["updated"] = now
        if len(conv["messages"]) == 1:
            conv["title"] = (msg or "图片对话")[:25]
            if len(conv["messages"]) == 1 and len(conv["title"]) > 25:
                conv["title"] += "..."

        attachments = list(self.attachments)
        self.attachments = []
        self._update_attach_bar()
        self._save_conv(self.current_conv)
        self._render_chat()

        # 切换为停止状态
        self._is_generating = True
        self.send_btn.config(text=self.l["stop"], bg="#888888", fg="#ffffff")

        self.chat_text.config(state="normal")
        self.chat_text.insert("end", f"⏳ {self.l['thinking']}\n\n", "thinking_tag")
        self.chat_text.config(state="disabled")
        self.chat_text.see("end")

        def worker():
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in conv["messages"][:-1]]
            try:
                resp = self.orch.process(msg, images=attachments, history=history)
            except Exception as e:
                resp = f"错误: {e}"
            self.root.after(0, lambda: self._on_response(resp))

        threading.Thread(target=worker, daemon=True).start()

    def _stop_generation(self):
        self.orch.stop()
        self._is_generating = False
        self.send_btn.config(text=self.l["send"], bg=self.t["btn_bg"], fg=self.t["btn_fg"])

        self.chat_text.config(state="normal")
        ranges = self.chat_text.tag_ranges("thinking_tag")
        if ranges:
            self.chat_text.delete(ranges[0], ranges[1])
        self.chat_text.insert("end", "[已停止生成]\n\n", "sys")
        self.chat_text.config(state="disabled")
        self.chat_text.see("end")

    def _on_response(self, resp):
        self.chat_text.config(state="normal")
        ranges = self.chat_text.tag_ranges("thinking_tag")
        if ranges:
            self.chat_text.delete(ranges[0], ranges[1])
        self.chat_text.config(state="disabled")

        conv = self.conversations.get(self.current_conv)
        if conv:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conv["messages"].append(
                {"role": "assistant", "content": resp, "timestamp": now})
            conv["updated"] = now
            self._save_conv(self.current_conv)
            self._last_ai_response = resp

        self._render_chat()
        self._is_generating = False
        self.send_btn.config(text=self.l["send"], bg=self.t["btn_bg"], fg=self.t["btn_fg"])

    # ================================================================
    # 复制
    # ================================================================
    def _copy_last_response(self):
        if self._last_ai_response:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._last_ai_response)
            self.add_log("已复制最后一条AI回复到剪贴板")
        else:
            self.add_log("没有可复制的AI回复")

    # ================================================================
    # 附件
    # ================================================================
    def _attach_file(self):
        paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.gif *.webp *.bmp")])
        if paths:
            self.attachments.extend(paths)
            self._update_attach_bar()
            self.add_log(f"已附加 {len(paths)} 个文件")

    def _update_attach_bar(self):
        if not self.attachments:
            self.attach_bar.grid_remove()
            return
        names = [os.path.basename(p) for p in self.attachments]
        display = "📎 已附加: " + ", ".join(names)
        if len(display) > 80:
            display = display[:77] + "..."
        self.attach_label.config(text=display)
        self.attach_bar.grid()

    def _clear_attachments(self):
        self.attachments = []
        self._update_attach_bar()
        self.add_log("已清除所有附件")

    # ================================================================
    # 日志
    # ================================================================
    def add_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"

        def _insert():
            self.log_text.config(state="normal")
            self.log_text.insert("end", line)
            self.log_text.config(state="disabled")
            self.log_text.see("end")

        if threading.current_thread() is threading.main_thread():
            _insert()
        else:
            self.root.after(0, _insert)

    # ================================================================
    # 设置
    # ================================================================
    def _change_theme(self, event=None):
        val = "dark" if self.theme_cb.get().startswith("深色") or self.theme_cb.get().startswith("Dark") else "light"
        self.cfg.set("theme", val)
        messagebox.showinfo("", "主题将在重启后生效")

    def _change_lang(self, event=None):
        val = "zh" if self.lang_cb.get() == "中文" else "en"
        self.cfg.set("language", val)
        messagebox.showinfo("", "语言将在重启后生效")

    def _browse_storage(self):
        path = filedialog.askdirectory(title="选择存储文件夹")
        if path:
            self.cfg.set("storage_path", path)
            self._load_all_conversations()

    # ================================================================
    # 自动更新
    # ================================================================
    def _auto_check_update(self):
        if not HAS_UPDATER:
            return

        def cb(has_update, version, changelog):
            if has_update:
                self.root.after(0, lambda: self._ask_update(version, changelog))

        self.updater.check_async(callback=cb)

    def _ask_update(self, version, changelog):
        msg = (f"发现新版本 v{version}\n\n"
               f"更新内容:\n{changelog}\n\n"
               f"是否立即更新？")
        if messagebox.askyesno("软件更新", msg):
            self._do_update()

    def _do_update(self):
        win = tk.Toplevel(self.root)
        win.title("更新中...")
        win.geometry("400x150")
        win.configure(bg=self.t["bg"])
        win.resizable(False, False)
        win.grab_set()
        tk.Label(win, text="正在更新，请勿关闭...",
                 bg=self.t["bg"], fg=self.t["text"],
                 font=("Microsoft YaHei", 11)).pack(pady=(20, 10))
        bar = ttk.Progressbar(win, length=350, mode="determinate")
        bar.pack(pady=5)
        status = tk.Label(win, text="准备中...",
                          bg=self.t["bg"], fg=self.t["muted"],
                          font=("Microsoft YaHei", 9))
        status.pack(pady=5)

        def on_progress(pct, msg):
            if pct >= 0:
                self.root.after(0, lambda: bar.configure(value=pct))
            self.root.after(0, lambda: status.configure(text=msg))

        def worker():
            ok = self.updater.download_and_update(progress_callback=on_progress)
            self.root.after(0, win.destroy)
            if ok:
                self.root.after(0, lambda: messagebox.showinfo(
                    "更新完成", "更新成功！请重启软件。"))
            else:
                self.root.after(0, lambda: messagebox.showerror(
                    "更新失败", "更新出错，请稍后重试。"))

        threading.Thread(target=worker, daemon=True).start()

    def _manual_check_update(self):
        if not HAS_UPDATER:
            return

        def cb(has_update, version, changelog):
            if has_update:
                self.root.after(0, lambda: self._ask_update(version, changelog))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "检查更新", f"已是最新版本 v{self.updater.current_version}"))

        self.updater.check_async(callback=cb)

    # ================================================================
    # 运行
    # ================================================================
    def run(self):
        self.root.mainloop()