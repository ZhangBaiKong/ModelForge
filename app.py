#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型整合 GUI (ModelForge GUI)
三栏布局：左侧对话列表 | 中间对话区 | 右侧模型面板+日志+设置
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import threading
from datetime import datetime

from config_manager import ConfigManager
from engine import Orchestrator
from updater import Updater


# ================================================================
# 主题配色 (Themes)
# ================================================================
THEMES = {
    "dark": {
        "bg": "#1a1a2e", "surface": "#16213e", "surface2": "#0f3460",
        "accent": "#e94560", "text": "#eaeaea", "muted": "#7f8c8d",
        "entry_bg": "#16213e", "entry_fg": "#eaeaea",
        "btn_bg": "#e94560", "btn_fg": "#ffffff",
        "list_bg": "#16213e", "list_fg": "#eaeaea", "list_sel": "#0f3460",
        "chat_user": "#7aa2f7", "chat_ai": "#9ece6a",
    },
    "light": {
        "bg": "#f0f0f0", "surface": "#ffffff", "surface2": "#e8e8e8",
        "accent": "#2563eb", "text": "#1f2937", "muted": "#9ca3af",
        "entry_bg": "#ffffff", "entry_fg": "#1f2937",
        "btn_bg": "#2563eb", "btn_fg": "#ffffff",
        "list_bg": "#ffffff", "list_fg": "#1f2937", "list_sel": "#dbeafe",
        "chat_user": "#2563eb", "chat_ai": "#16a34a",
    },
}


# ================================================================
# 多语言 (i18n)
# ================================================================
LANG = {
    "zh": {
        "title": "模型整合 (ModelForge)",
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
        "send": "发送 (Ctrl+Enter)",
        "cfg_model": "配置模型 (Model Config)",
        "m_name": "名称 (Name)",
        "m_dir": "方向 (Direction)",
        "m_url": "API 地址 (API URL)",
        "m_key": "API 密钥 (API Key)",
        "m_id": "模型名 (Model ID)",
        "m_temp": "温度 (Temperature)",
        "m_tokens": "最大 Token (Max Tokens)",
        "m_prompt": "系统提示词 (System Prompt)",
        "test": "测试连接 (Test)",
        "save": "保存", "cancel": "取消",
        "thinking": "思考中...",
        "welcome": "欢迎使用模型整合 (ModelForge)！\n请先在右侧配置主模型。",
        "del_confirm": "确认删除此对话？",
        "del_model_confirm": "确认删除此模型？",
        "dirs": [
            "文本对话 (Chat)", "代码生成 (Code)",
            "图片识别 (Vision)", "界面生成 (UI Gen)",
            "翻译 (Translate)", "自定义 (Custom)",
        ],
    },
    "en": {
        "title": "ModelForge",
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
        "send": "Send (Ctrl+Enter)",
        "cfg_model": "Model Config",
        "m_name": "Name", "m_dir": "Direction",
        "m_url": "API URL", "m_key": "API Key",
        "m_id": "Model ID", "m_temp": "Temperature",
        "m_tokens": "Max Tokens", "m_prompt": "System Prompt",
        "test": "Test Connection", "save": "Save", "cancel": "Cancel",
        "thinking": "Thinking...",
        "welcome": "Welcome to ModelForge!\nPlease configure the main model first.",
        "del_confirm": "Delete this conversation?",
        "del_model_confirm": "Delete this model?",
        "dirs": ["Chat", "Code", "Vision", "UI Gen", "Translate", "Custom"],
    },
}


# ================================================================
# 模型配置弹窗 (Model Config Dialog)
# ================================================================
class ModelConfigDialog(tk.Toplevel):
    def __init__(self, parent, theme, lang, model_data=None, callback=None):
        super().__init__(parent)
        self.theme = theme
        self.lang = lang
        self.model_data = model_data or {}
        self.callback = callback

        self.title(lang["cfg_model"])
        self.geometry("500x650")
        self.configure(bg=theme["bg"])
        self.resizable(False, False)
        self.grab_set()

        self._show_key = False
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
        frame = tk.Frame(self, bg=t["bg"], padx=20, pady=10)
        frame.pack(fill="both", expand=True)

        self._lbl(frame, l["m_name"])
        self.w_name = self._entry(frame)

        self._lbl(frame, l["m_dir"])
        self.w_dir = ttk.Combobox(frame, values=l["dirs"], state="readonly")
        self.w_dir.pack(fill="x", pady=(0, 4))

        self._lbl(frame, l["m_url"])
        self.w_url = self._entry(frame)

        self._lbl(frame, l["m_key"])
        key_frame = tk.Frame(frame, bg=t["bg"])
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

        self._lbl(frame, l["m_id"])
        self.w_model = self._entry(frame)

        self._lbl(frame, l["m_temp"])
        self.w_temp = tk.Scale(
            frame, from_=0, to=2, resolution=0.1, orient="horizontal",
            bg=t["bg"], fg=t["text"], highlightthickness=0,
            troughcolor=t["surface2"], activebackground=t["accent"],
        )
        self.w_temp.set(0.7)
        self.w_temp.pack(fill="x", pady=(0, 4))

        self._lbl(frame, l["m_tokens"])
        self.w_tokens = self._entry(frame)
        self.w_tokens.insert(0, "4096")

        self._lbl(frame, l["m_prompt"])
        self.w_prompt = tk.Text(
            frame, height=4, bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat",
            font=("Microsoft YaHei", 9), wrap="word",
        )
        self.w_prompt.pack(fill="x", pady=(0, 10))

        btn_frame = tk.Frame(frame, bg=t["bg"])
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

    def _toggle_key(self):
        self._show_key = not self._show_key
        self.w_key.config(show="" if self._show_key else "*")

    def _load(self, d):
        self.w_name.insert(0, d.get("name", ""))
        self.w_dir.set(d.get("direction", ""))
        self.w_url.insert(0, d.get("api_url", ""))
        self.w_key.insert(0, d.get("api_key", ""))
        self.w_model.insert(0, d.get("model_name", ""))
        self.w_temp.set(d.get("temperature", 0.7))
        self.w_tokens.delete(0, "end")
        self.w_tokens.insert(0, str(d.get("max_tokens", 4096)))
        self.w_prompt.insert("1.0", d.get("system_prompt", ""))

    def _get_data(self):
        return {
            "name": self.w_name.get().strip(),
            "direction": self.w_dir.get().strip(),
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
                h = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {d['api_key']}",
                }
                p = {
                    "model": d["model_name"],
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                }
                r = rq.post(d["api_url"], headers=h, json=p, timeout=15)
                r.raise_for_status()
                self.after(0, lambda: messagebox.showinfo(
                    "成功", "连接正常！"))
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda: messagebox.showerror(
                    "失败", error_msg))

        threading.Thread(target=go, daemon=True).start()

    def _save(self):
        d = self._get_data()
        if not d["name"]:
            messagebox.showwarning("提示", "请填写模型名称")
            return
        if self.callback:
            self.callback(d)
        self.destroy()


# ================================================================
# 主应用 (Main Application)
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

        self._setup_window()
        self._create_left_panel()
        self._create_center_panel()
        self._create_right_panel()
        self._load_all_conversations()
        self._refresh_model_list()
        self.updater = Updater(log_callback=self.add_log)
        self.add_log("应用已启动 (Application started)")
        self.root.after(5000, self._auto_check_update)

    # ────────────────────────────────────────
    # 窗口基础设置
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
            font=("Microsoft YaHei", 14, "bold"),
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
        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat",
            font=("Microsoft YaHei", 9),
        )
        search_entry.pack(fill="x")
        hint = l["search_hint"]
        search_entry.insert(0, hint)
        search_entry.bind(
            "<FocusIn>",
            lambda e: search_entry.delete(0, "end")
            if search_entry.get() == hint else None,
        )

        self.conv_lb = tk.Listbox(
            panel, bg=t["list_bg"], fg=t["list_fg"],
            selectbackground=t["list_sel"], selectforeground=t["list_fg"],
            relief="flat", font=("Microsoft YaHei", 10),
            activestyle="none", highlightthickness=0,
        )
        self.conv_lb.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        self.conv_lb.bind("<<ListboxSelect>>", self._on_conv_select)
        self.conv_lb.bind("<Button-3>", self._conv_context_menu)

        scrollbar = tk.Scrollbar(panel, command=self.conv_lb.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.conv_lb.config(yscrollcommand=scrollbar.set)

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
        chat_scrollbar = tk.Scrollbar(panel, command=self.chat_text.yview)
        chat_scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_text.config(yscrollcommand=chat_scrollbar.set)

        self.chat_text.tag_configure(
            "user_tag", foreground=t["chat_user"],
            font=("Microsoft YaHei", 9, "bold"))
        self.chat_text.tag_configure(
            "ai_tag", foreground=t["chat_ai"],
            font=("Microsoft YaHei", 9, "bold"))
        self.chat_text.tag_configure(
            "msg", foreground=t["text"], font=("Microsoft YaHei", 10),
            lmargin1=10, lmargin2=10)
        self.chat_text.tag_configure(
            "sys", foreground=t["muted"],
            font=("Microsoft YaHei", 9, "italic"), justify="center")
        self.chat_text.tag_configure("thinking_tag", foreground=t["accent"])
        self.chat_text.tag_configure(
            "file_tag", foreground="#e0a030",
            font=("Microsoft YaHei", 9, "italic"))

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
        input_frame = tk.Frame(panel, bg=t["bg"])
        input_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        input_frame.columnconfigure(1, weight=1)

        tk.Button(
            input_frame, text="📎", command=self._attach_file,
            bg=t["surface2"], fg=t["text"], relief="flat", width=3,
        ).grid(row=0, column=0, padx=(0, 4))

        self.input_text = tk.Text(
            input_frame, bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat",
            font=("Microsoft YaHei", 10), height=3, wrap="word",
            highlightthickness=0,
        )
        self.input_text.grid(row=0, column=1, sticky="ew")
        self.input_text.bind("<Control-Return>", lambda e: self._send())

        self.send_btn = tk.Button(
            input_frame, text=l["send"], command=self._send,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat", padx=16,
            font=("Microsoft YaHei", 10, "bold"),
        )
        self.send_btn.grid(row=0, column=2, padx=(4, 0))

        self._show_welcome()

    # ────────────────────────────────────────
    # 右栏：模型+日志+设置
    # ────────────────────────────────────────
    def _create_right_panel(self):
        t, l = self.t, self.l
        panel = tk.Frame(self.root, bg=t["bg"])
        panel.grid(row=0, column=2, sticky="nsew", padx=(2, 5), pady=5)
        panel.rowconfigure(0, weight=2)
        panel.rowconfigure(1, weight=3)
        panel.rowconfigure(2, weight=0)
        panel.columnconfigure(0, weight=1)

        model_frame = tk.LabelFrame(
            panel, text=f" {l['models']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        model_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
        model_frame.rowconfigure(0, weight=1)
        model_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Model.Treeview", background=t["surface"], foreground=t["text"],
            fieldbackground=t["surface"], rowheight=26,
            font=("Microsoft YaHei", 9))
        style.configure(
            "Model.Treeview.Heading", background=t["surface2"],
            foreground=t["muted"], font=("Microsoft YaHei", 9))

        self.model_tree = ttk.Treeview(
            model_frame, style="Model.Treeview",
            columns=("role", "dir"), show="tree headings", height=5)
        self.model_tree.heading("#0", text=l["m_name"])
        self.model_tree.heading("role", text="角色")
        self.model_tree.heading("dir", text=l["m_dir"])
        self.model_tree.column("#0", width=100)
        self.model_tree.column("role", width=50)
        self.model_tree.column("dir", width=80)
        self.model_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.model_tree.bind("<Double-1>", self._edit_model)
        self.model_tree.bind("<Button-3>", self._model_context_menu)

        tk.Button(
            model_frame, text=l["add_model"], command=self._add_model,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat",
            font=("Microsoft YaHei", 9),
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        log_frame = tk.LabelFrame(
            panel, text=f" {l['logs']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        log_frame.grid(row=1, column=0, sticky="nsew", pady=3)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame, bg=t["surface"], fg=t["muted"], relief="flat",
            font=("Consolas", 9), wrap="word", state="disabled",
            highlightthickness=0, padx=6, pady=4)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        log_scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        settings_frame = tk.LabelFrame(
            panel, text=f" {l['settings']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        settings_frame.grid(row=2, column=0, sticky="ew", pady=(3, 0))

        row1 = tk.Frame(settings_frame, bg=t["surface"])
        row1.pack(fill="x", padx=8, pady=2)
        tk.Label(
            row1, text=l["theme"], bg=t["surface"], fg=t["text"],
            font=("Microsoft YaHei", 9)).pack(side="left")
        self.theme_cb = ttk.Combobox(
            row1, values=[l["dark"], l["light"]], state="readonly", width=10)
        self.theme_cb.set(
            l["dark"] if self.cfg.get("theme") == "dark" else l["light"])
        self.theme_cb.pack(side="right")
        self.theme_cb.bind("<<ComboboxSelected>>", self._change_theme)

        row2 = tk.Frame(settings_frame, bg=t["surface"])
        row2.pack(fill="x", padx=8, pady=2)
        tk.Label(
            row2, text=l["lang"], bg=t["surface"], fg=t["text"],
            font=("Microsoft YaHei", 9)).pack(side="left")
        self.lang_cb = ttk.Combobox(
            row2, values=["中文", "English"], state="readonly", width=10)
        self.lang_cb.set(
            "中文" if self.cfg.get("language") == "zh" else "English")
        self.lang_cb.pack(side="right")
        self.lang_cb.bind("<<ComboboxSelected>>", self._change_lang)

        row3 = tk.Frame(settings_frame, bg=t["surface"])
        row3.pack(fill="x", padx=8, pady=(2, 6))
        tk.Label(
            row3, text=l["storage"], bg=t["surface"], fg=t["text"],
            font=("Microsoft YaHei", 9)).pack(side="left")
        tk.Button(
            row3, text=l["browse"], command=self._browse_storage,
            bg=t["surface2"], fg=t["text"], relief="flat").pack(side="right")
        

        row4 = tk.Frame(settings_frame, bg=t["surface"])
        row4.pack(fill="x", padx=8, pady=(2, 6))
        tk.Button(
            row4, text="检查更新 (Check Update)",
            command=self._manual_check_update,
            bg=t["surface2"], fg=t["text"], relief="flat").pack(fill="x")
        


        def _manual_check_update(self):
             def cb(has_update, version, changelog):
                 if has_update:
                     self.root.after(0, lambda: self._ask_update(version, changelog))
                 else:
                     self.root.after(0, lambda: messagebox.showinfo(
                         "检查更新", f"已是最新版本 v{self.updater.current_version}"))
             self.updater.check_async(callback=cb)    

    # ================================================================
    # 对话管理
    # ================================================================
    def _load_all_conversations(self):
        storage_path = self.cfg.get("storage_path", "./conversations")
        os.makedirs(storage_path, exist_ok=True)
        self.conversations = {}
        for filename in os.listdir(storage_path):
            if filename.endswith(".json"):
                try:
                    filepath = os.path.join(storage_path, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        conv = json.load(f)
                        self.conversations[conv["id"]] = conv
                except Exception:
                    pass
        self._refresh_conv_list()

    def _save_conv(self, conv_id):
        conv = self.conversations.get(conv_id)
        if not conv:
            return
        storage_path = self.cfg.get("storage_path", "./conversations")
        os.makedirs(storage_path, exist_ok=True)
        filepath = os.path.join(storage_path, f"{conv_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(conv, f, ensure_ascii=False, indent=2)

    def _new_conv(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversations[conv_id] = {
            "id": conv_id, "title": "新对话 (New Chat)",
            "created": now, "updated": now,
            "pinned": False, "messages": [],
        }
        self._save_conv(conv_id)
        self._refresh_conv_list()
        self._switch_conv(conv_id)

    def _refresh_conv_list(self):
        query = self.search_var.get().strip().lower()
        hint = self.l["search_hint"].lower()
        if query == hint:
            query = ""

        self.conv_lb.delete(0, "end")
        self.conv_id_list = []

        pinned = sorted(
            [c for c in self.conversations.values() if c.get("pinned")],
            key=lambda c: c.get("updated", ""), reverse=True)
        normal = sorted(
            [c for c in self.conversations.values() if not c.get("pinned")],
            key=lambda c: c.get("updated", ""), reverse=True)

        for conv in pinned + normal:
            if query and query not in conv["title"].lower():
                continue
            prefix = "📌 " if conv.get("pinned") else ""
            self.conv_lb.insert("end", f"{prefix}{conv['title']}")
            self.conv_id_list.append(conv["id"])

    def _on_conv_select(self, event=None):
        sel = self.conv_lb.curselection()
        if not sel:
            return
        self._switch_conv(self.conv_id_list[sel[0]])

    def _switch_conv(self, conv_id):
        if conv_id not in self.conversations:
            return
        self.current_conv = conv_id
        self._render_chat()

    def _render_chat(self):
        self.chat_text.config(state="normal")
        self.chat_text.delete("1.0", "end")
        conv = self.conversations.get(self.current_conv)
        if not conv:
            self.chat_text.config(state="disabled")
            return
        for msg in conv["messages"]:
            ts = msg.get("timestamp", "")[-8:]
            if msg["role"] == "user":
                self.chat_text.insert("end", f"你  {ts}\n", "user_tag")
                attachments = msg.get("attachments", [])
                if attachments:
                    file_str = ", ".join(attachments)
                    self.chat_text.insert(
                        "end", f"📎 附件: {file_str}\n", "file_tag")
                self.chat_text.insert(
                    "end", f"{msg['content']}\n\n", "msg")
            else:
                self.chat_text.insert("end", f"AI  {ts}\n", "ai_tag")
                self.chat_text.insert(
                    "end", f"{msg['content']}\n\n", "msg")
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
        conv_id = self.conv_id_list[idx]
        conv = self.conversations.get(conv_id, {})

        menu = tk.Menu(self.root, tearoff=0, bg=self.t["surface"],
                       fg=self.t["text"], relief="flat")
        if conv.get("pinned"):
            menu.add_command(label=self.l["unpin"],
                             command=lambda: self._pin_conv(conv_id, False))
        else:
            menu.add_command(label=self.l["pin"],
                             command=lambda: self._pin_conv(conv_id, True))
        menu.add_command(label=self.l["rename"],
                         command=lambda: self._rename_conv(conv_id))
        menu.add_command(label=self.l["export"],
                         command=lambda: self._export_conv(conv_id))
        menu.add_separator()
        menu.add_command(label=self.l["delete"],
                         command=lambda: self._delete_conv(conv_id))
        menu.tk_popup(event.x_root, event.y_root)

    def _pin_conv(self, conv_id, pinned):
        self.conversations[conv_id]["pinned"] = pinned
        self._save_conv(conv_id)
        self._refresh_conv_list()

    def _rename_conv(self, conv_id):
        old_title = self.conversations[conv_id]["title"]
        new_title = simpledialog.askstring(
            self.l["rename"], self.l["rename"],
            initialvalue=old_title, parent=self.root)
        if new_title and new_title.strip():
            self.conversations[conv_id]["title"] = new_title.strip()
            self._save_conv(conv_id)
            self._refresh_conv_list()

    def _export_conv(self, conv_id):
        conv = self.conversations.get(conv_id)
        if not conv:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("JSON", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            if path.endswith(".json"):
                json.dump(conv, f, ensure_ascii=False, indent=2)
            else:
                for msg in conv["messages"]:
                    role = "你" if msg["role"] == "user" else "AI"
                    ts = msg.get("timestamp", "")
                    f.write(f"[{role}] {ts}\n{msg['content']}\n\n")

    def _delete_conv(self, conv_id):
        if not messagebox.askyesno("", self.l["del_confirm"]):
            return
        storage_path = self.cfg.get("storage_path", "./conversations")
        filepath = os.path.join(storage_path, f"{conv_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        self.conversations.pop(conv_id, None)
        if self.current_conv == conv_id:
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
            self.model_tree.insert(
                "", "end", iid="main", text=main.get("name", "未命名"),
                values=(self.l["main"], main.get("direction", "")))

        for i, sub in enumerate(self.cfg.get_sub_models()):
            self.model_tree.insert(
                "", "end", iid=f"sub_{i}", text=sub.get("name", "未命名"),
                values=(self.l["sub"], sub.get("direction", "")))

    def _add_model(self):
        def on_save(data):
            choice = messagebox.askyesno(
                "角色选择 (Role)",
                "设为主模型？\n\n是(Yes) = 主模型 (Main)\n否(No) = 副模型 (Sub)",
                parent=self.root)
            if choice:
                data["id"] = "main"
                self.cfg.set_main_model(data)
            else:
                data["id"] = f"sub_{len(self.cfg.get_sub_models())}"
                self.cfg.add_sub_model(data)
            self._refresh_model_list()
            self.add_log(f"已添加模型: {data['name']}")

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

            def on_save(d):
                d["id"] = "main"
                self.cfg.set_main_model(d)
                self._refresh_model_list()
                self.add_log(f"已更新主模型: {d['name']}")

            ModelConfigDialog(
                self.root, self.t, self.l,
                model_data=data, callback=on_save)
        else:
            idx = int(iid.split("_")[1])
            subs = self.cfg.get_sub_models()
            if idx >= len(subs):
                return

            def on_save(d):
                d["id"] = f"sub_{idx}"
                self.cfg.update_sub_model(idx, d)
                self._refresh_model_list()
                self.add_log(f"已更新副模型: {d['name']}")

            ModelConfigDialog(
                self.root, self.t, self.l,
                model_data=subs[idx], callback=on_save)

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
        self.add_log("已删除模型 (Model deleted)")

    # ================================================================
    # 发送消息
    # ================================================================
    def _send(self):
        msg = self.input_text.get("1.0", "end").strip()
        if not msg and not self.attachments:
            return
        self.input_text.delete("1.0", "end")

        if not self.current_conv:
            title = (msg or "图片对话")[:25]
            if len(msg or "图片对话") > 25:
                title += "..."
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.conversations[conv_id] = {
                "id": conv_id, "title": title,
                "created": now, "updated": now,
                "pinned": False, "messages": [],
            }
            self.current_conv = conv_id
            self._refresh_conv_list()
            self._switch_conv(conv_id)

        conv = self.conversations[self.current_conv]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        file_names = [os.path.basename(p) for p in self.attachments]
        conv["messages"].append({
            "role": "user",
            "content": msg,
            "timestamp": now,
            "attachments": file_names,
        })
        conv["updated"] = now

        if len(conv["messages"]) == 1:
            conv["title"] = (msg or "图片对话")[:25]
            if len(msg or "图片对话") > 25:
                conv["title"] += "..."
            self._refresh_conv_list()

        attachments = list(self.attachments)
        self.attachments = []
        self._update_attach_bar()

        self._save_conv(self.current_conv)
        self._render_chat()

        self.chat_text.config(state="normal")
        self.chat_text.insert(
            "end", f"⏳ {self.l['thinking']}\n\n", "thinking_tag")
        self.chat_text.config(state="disabled")
        self.chat_text.see("end")
        self.send_btn.config(state="disabled")

        def worker():
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in conv["messages"][:-1]]
            try:
                resp = self.orch.process(
                    msg, images=attachments, history=history)
            except Exception as e:
                resp = f"错误: {e}"
            self.root.after(0, lambda: self._on_response(resp))

        threading.Thread(target=worker, daemon=True).start()

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

        self._render_chat()
        self.send_btn.config(state="normal")

    # ================================================================
    # 附件
    # ================================================================
    def _attach_file(self):
        paths = filedialog.askopenfilenames(
            title="选择图片 (Select Images)",
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
        val = "dark" if self.theme_cb.get().startswith(self.l["dark"][:2]) else "light"
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

    def run(self):
        self.root.mainloop()


        # ================================================================
    # 自动更新 (Auto Update)
    # ================================================================
    def _auto_check_update(self):
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