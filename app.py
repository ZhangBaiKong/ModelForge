#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模型整合 GUI"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import os
import threading
from datetime import datetime

from config_manager import ConfigManager
from engine import Orchestrator


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

LANG = {
    "zh": {
        "title": "模型整合", "new_chat": "＋ 新建对话",
        "search_hint": "搜索对话...", "pin": "置顶", "unpin": "取消置顶",
        "rename": "重命名", "delete": "删除", "export": "导出",
        "models": "模型", "add_model": "＋ 添加模型",
        "main": "主模型", "sub": "副模型",
        "logs": "运行日志", "settings": "软件设置",
        "theme": "主题", "dark": "深色", "light": "浅色",
        "lang": "语言", "storage": "存储路径", "browse": "浏览",
        "send": "发送", "cfg_model": "配置模型",
        "m_name": "名称", "m_dir": "方向", "m_url": "API地址",
        "m_key": "API密钥", "m_id": "模型名", "m_temp": "温度",
        "m_tokens": "最大Token", "m_prompt": "系统提示词",
        "test": "测试连接", "save": "保存", "cancel": "取消",
        "thinking": "思考中...",
        "welcome": "欢迎使用模型整合！\n请先在右侧配置主模型。",
        "del_confirm": "确认删除此对话？",
        "del_model_confirm": "确认删除此模型？",
        "no_main": "请先配置主模型",
        "dirs": ["文本对话", "代码生成", "图片识别", "界面生成", "翻译", "自定义"],
    },
    "en": {
        "title": "ModelForge", "new_chat": "+ New Chat",
        "search_hint": "Search...", "pin": "Pin", "unpin": "Unpin",
        "rename": "Rename", "delete": "Delete", "export": "Export",
        "models": "Models", "add_model": "+ Add Model",
        "main": "Main", "sub": "Sub",
        "logs": "Logs", "settings": "Settings",
        "theme": "Theme", "dark": "Dark", "light": "Light",
        "lang": "Language", "storage": "Storage", "browse": "Browse",
        "send": "Send", "cfg_model": "Configure Model",
        "m_name": "Name", "m_dir": "Direction", "m_url": "API URL",
        "m_key": "API Key", "m_id": "Model ID", "m_temp": "Temperature",
        "m_tokens": "Max Tokens", "m_prompt": "System Prompt",
        "test": "Test", "save": "Save", "cancel": "Cancel",
        "thinking": "Thinking...",
        "welcome": "Welcome!\nPlease configure the main model first.",
        "del_confirm": "Delete this conversation?",
        "del_model_confirm": "Delete this model?",
        "no_main": "Please configure the main model first",
        "dirs": ["Chat", "Code", "Vision", "UI Gen", "Translate", "Custom"],
    },
}


class ModelConfigDialog(tk.Toplevel):
    def __init__(self, parent, theme, lang, model_data=None, callback=None):
        super().__init__(parent)
        self.theme = theme
        self.lang = lang
        self.model_data = model_data or {}
        self.callback = callback

        self.title(lang["cfg_model"])
        self.geometry("480x620")
        self.configure(bg=theme["bg"])
        self.resizable(False, False)
        self.grab_set()

        self._show_key = False
        self._build()
        if model_data:
            self._load(model_data)

    def _lbl(self, p, text):
        tk.Label(
            p, text=text, bg=self.theme["bg"], fg=self.theme["muted"],
            font=("Microsoft YaHei", 9), anchor="w",
        ).pack(fill="x", pady=(8, 2))

    def _entry(self, p):
        e = tk.Entry(
            p, bg=self.theme["entry_bg"], fg=self.theme["entry_fg"],
            insertbackground=self.theme["text"], relief="flat",
            font=("Consolas", 10),
        )
        e.pack(fill="x", pady=(0, 4))
        return e

    def _build(self):
        t, l = self.theme, self.lang
        f = tk.Frame(self, bg=t["bg"], padx=20, pady=10)
        f.pack(fill="both", expand=True)

        self._lbl(f, l["m_name"])
        self.w_name = self._entry(f)

        self._lbl(f, l["m_dir"])
        self.w_dir = ttk.Combobox(f, values=l["dirs"], state="readonly")
        self.w_dir.pack(fill="x", pady=(0, 4))

        self._lbl(f, l["m_url"])
        self.w_url = self._entry(f)

        self._lbl(f, l["m_key"])
        kf = tk.Frame(f, bg=t["bg"])
        kf.pack(fill="x", pady=(0, 4))
        self.w_key = tk.Entry(
            kf, show="*", bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat", font=("Consolas", 10),
        )
        self.w_key.pack(side="left", fill="x", expand=True)
        tk.Button(
            kf, text="👁", command=self._toggle_key,
            bg=t["surface"], fg=t["text"], relief="flat", width=3,
        ).pack(side="right", padx=(4, 0))

        self._lbl(f, l["m_id"])
        self.w_model = self._entry(f)

        self._lbl(f, l["m_temp"])
        self.w_temp = tk.Scale(
            f, from_=0, to=2, resolution=0.1, orient="horizontal",
            bg=t["bg"], fg=t["text"], highlightthickness=0,
            troughcolor=t["surface2"], activebackground=t["accent"],
        )
        self.w_temp.set(0.7)
        self.w_temp.pack(fill="x", pady=(0, 4))

        self._lbl(f, l["m_tokens"])
        self.w_tokens = self._entry(f)
        self.w_tokens.insert(0, "4096")

        self._lbl(f, l["m_prompt"])
        self.w_prompt = tk.Text(
            f, height=4, bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat",
            font=("Microsoft YaHei", 9), wrap="word",
        )
        self.w_prompt.pack(fill="x", pady=(0, 10))

        bf = tk.Frame(f, bg=t["bg"])
        bf.pack(fill="x")
        tk.Button(
            bf, text=l["test"], command=self._test,
            bg=t["surface2"], fg=t["text"], relief="flat", padx=12,
        ).pack(side="left")
        tk.Button(
            bf, text=l["save"], command=self._save,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat", padx=16,
        ).pack(side="right", padx=(4, 0))
        tk.Button(
            bf, text=l["cancel"], command=self.destroy,
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

    def _get(self):
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

    def _test(self):
        import requests as rq
        d = self._get()
        if not d["api_url"] or not d["api_key"]:
            messagebox.showwarning("提示", "请填写API地址和密钥")
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
                self.after(0, lambda: messagebox.showinfo("成功", "连接正常！"))
            except Exception as e:
                 error_msg = str(e)
                 self.after(0, lambda: messagebox.showerror("失败", error_msg))
        threading.Thread(target=go, daemon=True).start()

    def _save(self):
        d = self._get()
        if not d["name"]:
            messagebox.showwarning("提示", "请填写名称")
            return
        if self.callback:
            self.callback(d)
        self.destroy()


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
        self._create_left()
        self._create_center()
        self._create_right()
        self._load_all_conversations()
        self._refresh_model_list()
        self.add_log("应用已启动")

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

    def _create_left(self):
        t, l = self.t, self.l
        f = tk.Frame(self.root, bg=t["bg"])
        f.grid(row=0, column=0, sticky="nsew", padx=(5, 2), pady=5)
        f.rowconfigure(2, weight=1)
        f.columnconfigure(0, weight=1)

        tk.Label(
            f, text=l["title"], bg=t["bg"], fg=t["accent"],
            font=("Microsoft YaHei", 14, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=8, pady=(5, 8))

        tk.Button(
            f, text=l["new_chat"], command=self._new_conv,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat",
            font=("Microsoft YaHei", 9),
        ).grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))

        sf = tk.Frame(f, bg=t["bg"])
        sf.grid(row=1, column=0, sticky="ew", padx=8, pady=(32, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_conv_list())
        se = tk.Entry(
            sf, textvariable=self.search_var,
            bg=t["entry_bg"], fg=t["entry_fg"],
            insertbackground=t["text"], relief="flat",
            font=("Microsoft YaHei", 9),
        )
        se.pack(fill="x")
        hint = l["search_hint"]
        if hint:
            se.insert(0, hint)
            se.bind(
                "<FocusIn>",
                lambda e: se.delete(0, "end") if se.get() == hint else None,
            )

        self.conv_lb = tk.Listbox(
            f, bg=t["list_bg"], fg=t["list_fg"],
            selectbackground=t["list_sel"], selectforeground=t["list_fg"],
            relief="flat", font=("Microsoft YaHei", 10),
            activestyle="none", highlightthickness=0,
        )
        self.conv_lb.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        self.conv_lb.bind("<<ListboxSelect>>", self._on_conv_select)
        self.conv_lb.bind("<Button-3>", self._conv_context)

        sb = tk.Scrollbar(f, command=self.conv_lb.yview)
        sb.grid(row=2, column=1, sticky="ns")
        self.conv_lb.config(yscrollcommand=sb.set)

    def _create_center(self):
        t, l = self.t, self.l
        f = tk.Frame(self.root, bg=t["bg"])
        f.grid(row=0, column=1, sticky="nsew", padx=2, pady=5)
        f.rowconfigure(0, weight=1)
        f.columnconfigure(0, weight=1)

        self.chat_text = tk.Text(
            f, bg=t["surface"], fg=t["text"], relief="flat",
            font=("Microsoft YaHei", 10), wrap="word", state="disabled",
            insertbackground=t["text"], highlightthickness=0, padx=12, pady=8,
        )
        self.chat_text.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        csb = tk.Scrollbar(f, command=self.chat_text.yview)
        csb.grid(row=0, column=1, sticky="ns")
        self.chat_text.config(yscrollcommand=csb.set)

        self.chat_text.tag_configure(
            "user_tag", foreground=t["chat_user"],
            font=("Microsoft YaHei", 9, "bold"),
        )
        self.chat_text.tag_configure(
            "ai_tag", foreground=t["chat_ai"],
            font=("Microsoft YaHei", 9, "bold"),
        )
        self.chat_text.tag_configure(
            "msg", foreground=t["text"], font=("Microsoft YaHei", 10),
            lmargin1=10, lmargin2=10,
        )
        self.chat_text.tag_configure(
            "sys", foreground=t["muted"],
            font=("Microsoft YaHei", 9, "italic"), justify="center",
        )
        self.chat_text.tag_configure("thinking_tag", foreground=t["accent"])

        inp = tk.Frame(f, bg=t["bg"])
        inp.grid(row=1, column=0, columnspan=2, sticky="ew")
        inp.columnconfigure(1, weight=1)

        tk.Button(
            inp, text="📎", command=self._attach,
            bg=t["surface2"], fg=t["text"], relief="flat", width=3,
        ).grid(row=0, column=0, padx=(0, 4))

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

    def _create_right(self):
        t, l = self.t, self.l
        f = tk.Frame(self.root, bg=t["bg"])
        f.grid(row=0, column=2, sticky="nsew", padx=(2, 5), pady=5)
        f.rowconfigure(0, weight=2)
        f.rowconfigure(1, weight=3)
        f.rowconfigure(2, weight=0)
        f.columnconfigure(0, weight=1)

        mf = tk.LabelFrame(
            f, text=f" {l['models']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        mf.grid(row=0, column=0, sticky="nsew", pady=(0, 3))
        mf.rowconfigure(0, weight=1)
        mf.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Model.Treeview", background=t["surface"], foreground=t["text"],
            fieldbackground=t["surface"], rowheight=26,
            font=("Microsoft YaHei", 9),
        )
        style.configure(
            "Model.Treeview.Heading", background=t["surface2"],
            foreground=t["muted"], font=("Microsoft YaHei", 9),
        )

        self.model_tree = ttk.Treeview(
            mf, style="Model.Treeview", columns=("role", "dir"),
            show="tree headings", height=5,
        )
        self.model_tree.heading("#0", text=l["m_name"])
        self.model_tree.heading("role", text="角色")
        self.model_tree.heading("dir", text=l["m_dir"])
        self.model_tree.column("#0", width=100)
        self.model_tree.column("role", width=50)
        self.model_tree.column("dir", width=80)
        self.model_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.model_tree.bind("<Double-1>", self._edit_model)
        self.model_tree.bind("<Button-3>", self._model_ctx)

        tk.Button(
            mf, text=l["add_model"], command=self._add_model,
            bg=t["btn_bg"], fg=t["btn_fg"], relief="flat",
            font=("Microsoft YaHei", 9),
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        lf = tk.LabelFrame(
            f, text=f" {l['logs']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        lf.grid(row=1, column=0, sticky="nsew", pady=3)
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            lf, bg=t["surface"], fg=t["muted"], relief="flat",
            font=("Consolas", 9), wrap="word", state="disabled",
            highlightthickness=0, padx=6, pady=4,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        lsb = tk.Scrollbar(lf, command=self.log_text.yview)
        lsb.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=lsb.set)

        sf = tk.LabelFrame(
            f, text=f" {l['settings']} ", bg=t["surface"], fg=t["muted"],
            font=("Microsoft YaHei", 10, "bold"), relief="groove", bd=1,
            labelanchor="nw",
        )
        sf.grid(row=2, column=0, sticky="ew", pady=(3, 0))

        r1 = tk.Frame(sf, bg=t["surface"])
        r1.pack(fill="x", padx=8, pady=2)
        tk.Label(
            r1, text=l["theme"], bg=t["surface"], fg=t["text"],
            font=("Microsoft YaHei", 9),
        ).pack(side="left")
        self.theme_cb = ttk.Combobox(
            r1, values=[l["dark"], l["light"]], state="readonly", width=8,
        )
        self.theme_cb.set(
            l["dark"] if self.cfg.get("theme") == "dark" else l["light"]
        )
        self.theme_cb.pack(side="right")
        self.theme_cb.bind("<<ComboboxSelected>>", self._change_theme)

        r2 = tk.Frame(sf, bg=t["surface"])
        r2.pack(fill="x", padx=8, pady=2)
        tk.Label(
            r2, text=l["lang"], bg=t["surface"], fg=t["text"],
            font=("Microsoft YaHei", 9),
        ).pack(side="left")
        self.lang_cb = ttk.Combobox(
            r2, values=["中文", "English"], state="readonly", width=8,
        )
        self.lang_cb.set(
            "中文" if self.cfg.get("language") == "zh" else "English"
        )
        self.lang_cb.pack(side="right")
        self.lang_cb.bind("<<ComboboxSelected>>", self._change_lang)

        r3 = tk.Frame(sf, bg=t["surface"])
        r3.pack(fill="x", padx=8, pady=(2, 6))
        tk.Label(
            r3, text=l["storage"], bg=t["surface"], fg=t["text"],
            font=("Microsoft YaHei", 9),
        ).pack(side="left")
        tk.Button(
            r3, text=l["browse"], command=self._browse_storage,
            bg=t["surface2"], fg=t["text"], relief="flat",
        ).pack(side="right")

    # ── 对话管理 ──

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
        cid = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            key=lambda c: c.get("updated", ""), reverse=True,
        )
        normal = sorted(
            [c for c in self.conversations.values() if not c.get("pinned")],
            key=lambda c: c.get("updated", ""), reverse=True,
        )

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
        for m in c["messages"]:
            ts = m.get("timestamp", "")[-8:]
            if m["role"] == "user":
                self.chat_text.insert("end", f"你  {ts}\n", "user_tag")
                self.chat_text.insert("end", f"{m['content']}\n\n", "msg")
            else:
                self.chat_text.insert("end", f"AI  {ts}\n", "ai_tag")
                self.chat_text.insert("end", f"{m['content']}\n\n", "msg")
        self.chat_text.config(state="disabled")
        self.chat_text.see("end")

    def _show_welcome(self):
        self.chat_text.config(state="normal")
        self.chat_text.insert("end", self.l["welcome"] + "\n", "sys")
        self.chat_text.config(state="disabled")

    def _conv_context(self, event):
        idx = self.conv_lb.nearest(event.y)
        if idx < 0:
            return
        self.conv_lb.selection_set(idx)
        cid = self.conv_id_list[idx]
        c = self.conversations.get(cid, {})

        menu = tk.Menu(
            self.root, tearoff=0, bg=self.t["surface"],
            fg=self.t["text"], relief="flat",
        )
        if c.get("pinned"):
            menu.add_command(
                label=self.l["unpin"], command=lambda: self._pin(cid, False))
        else:
            menu.add_command(
                label=self.l["pin"], command=lambda: self._pin(cid, True))
        menu.add_command(
            label=self.l["rename"], command=lambda: self._rename(cid))
        menu.add_command(
            label=self.l["export"], command=lambda: self._export(cid))
        menu.add_separator()
        menu.add_command(
            label=self.l["delete"], command=lambda: self._delete_conv(cid))
        menu.tk_popup(event.x_root, event.y_root)

    def _pin(self, cid, val):
        self.conversations[cid]["pinned"] = val
        self._save_conv(cid)
        self._refresh_conv_list()

    def _rename(self, cid):
        old = self.conversations[cid]["title"]
        new = simpledialog.askstring(
            self.l["rename"], self.l["rename"],
            initialvalue=old, parent=self.root,
        )
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
            filetypes=[("Text", "*.txt"), ("JSON", "*.json")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            if path.endswith(".json"):
                json.dump(c, f, ensure_ascii=False, indent=2)
            else:
                for m in c["messages"]:
                    role = "你" if m["role"] == "user" else "AI"
                    ts = m.get("timestamp", "")
                    f.write(f"[{role}] {ts}\n{m['content']}\n\n")

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

    # ── 模型管理 ──

    def _refresh_model_list(self):
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
        main = self.cfg.get_main_model()
        if main:
            self.model_tree.insert(
                "", "end", iid="main", text=main.get("name", "未命名"),
                values=(self.l["main"], main.get("direction", "")),
            )
        for i, sub in enumerate(self.cfg.get_sub_models()):
            self.model_tree.insert(
                "", "end", iid=f"sub_{i}", text=sub.get("name", "未命名"),
                values=(self.l["sub"], sub.get("direction", "")),
            )

    def _add_model(self):
        def on_save(data):
            choice = messagebox.askyesno(
                "角色选择", "设为主模型？\n\n是 = 主模型\n否 = 副模型",
                parent=self.root,
            )
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
                self.root, self.t, self.l, model_data=data, callback=on_save)
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
                self.root, self.t, self.l, model_data=subs[idx],
                callback=on_save)

    def _model_ctx(self, event):
        sel = self.model_tree.selection()
        if not sel:
            return
        iid = sel[0]
        menu = tk.Menu(
            self.root, tearoff=0, bg=self.t["surface"],
            fg=self.t["text"], relief="flat",
        )
        menu.add_command(label="编辑", command=self._edit_model)
        menu.add_command(label="删除", command=lambda: self._del_model(iid))
        menu.tk_popup(event.x_root, event.y_root)

    def _del_model(self, iid):
        if not messagebox.askyesno("", self.l["del_model_confirm"]):
            return
        if iid == "main":
            self.cfg.set_main_model(None)
        else:
            idx = int(iid.split("_")[1])
            self.cfg.remove_sub_model(idx)
        self._refresh_model_list()
        self.add_log("已删除模型")

    # ── 发送消息 ──

    def _send(self):
        msg = self.input_text.get("1.0", "end").strip()
        if not msg:
            return
        self.input_text.delete("1.0", "end")

        if not self.current_conv:
            title = msg[:25] + ("..." if len(msg) > 25 else "")
            cid = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.conversations[cid] = {
                "id": cid, "title": title, "created": now, "updated": now,
                "pinned": False, "messages": [],
            }
            self.current_conv = cid
            self._refresh_conv_list()
            self._switch_conv(cid)

        conv = self.conversations[self.current_conv]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conv["messages"].append(
            {"role": "user", "content": msg, "timestamp": now})
        conv["updated"] = now

        if len(conv["messages"]) == 1:
            conv["title"] = msg[:25] + ("..." if len(msg) > 25 else "")
            self._refresh_conv_list()

        self._save_conv(self.current_conv)
        self._render_chat()

        self.chat_text.config(state="normal")
        self.chat_text.insert(
            "end", f"⏳ {self.l['thinking']}\n\n", "thinking_tag")
        self.chat_text.config(state="disabled")
        self.chat_text.see("end")
        self.send_btn.config(state="disabled")

        attachments = list(self.attachments)
        self.attachments = []

        def worker():
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in conv["messages"][:-1]
            ]
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

    # ── 附件 ──

    def _attach(self):
        paths = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.gif *.webp *.bmp")],
        )
        if paths:
            self.attachments.extend(paths)
            self.add_log(f"已附加 {len(paths)} 个文件")

    # ── 日志 ──

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

    # ── 设置 ──

    def _change_theme(self, event=None):
        val = "dark" if self.theme_cb.get() == self.l["dark"] else "light"
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