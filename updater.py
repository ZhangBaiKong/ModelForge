#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热更新模块 (Auto Updater)
从GitHub检查并下载最新版本
"""

import json
import os
import sys
import shutil
import zipfile
import tempfile
import threading
import requests


GITHUB_OWNER = "ZhangBaiKong"
GITHUB_REPO = "ModelForge"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main"
VERSION_FILE_URL = f"{GITHUB_RAW}/version.json"
CURRENT_VERSION = "0.0.1.0"

UPDATE_FILES = [
    "main.py", "app.py", "engine.py", "config_manager.py",
    "updater.py", "requirements.txt", "README.md", "version.json",
]


class Updater:
    def __init__(self, log_callback=None):
        self.log = log_callback or print
        self.current_version = CURRENT_VERSION
        self.update_available = False
        self.latest_version = None

    @staticmethod
    def _v_tuple(v):
        return tuple(int(x) for x in v.split("."))

    def _app_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def check_update(self):
        try:
            self.log("[更新] 正在检查版本...")
            resp = requests.get(VERSION_FILE_URL, timeout=30)
            if resp.status_code != 200:
                self.log("[更新] 无法获取版本信息")
                return False, self.current_version, ""

            data = resp.json()
            latest = data.get("version", "0.0.0.0")
            changelog = data.get("changelog", "")

            if self._v_tuple(latest) > self._v_tuple(self.current_version):
                self.latest_version = latest
                self.update_available = True
                self.log(f"[更新] 发现新版本: v{latest} (当前: v{self.current_version})")
                return True, latest, changelog

            self.log(f"[更新] 已是最新版本 v{self.current_version}")
            return False, self.current_version, ""
        except Exception as e:
            self.log(f"[更新] 网络不佳，跳过检查 {e}")
            return False, self.current_version, ""

    def download_and_update(self, progress_callback=None):
        if not self.update_available:
            return False

        def report(pct, msg):
            if progress_callback:
                progress_callback(pct, msg)
            self.log(f"[更新] {msg}")

        try:
            zip_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/refs/heads/main.zip"
            report(0, "正在下载更新...")

            resp = requests.get(zip_url, timeout=120, stream=True)
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            chunks = []
            for chunk in resp.iter_content(8192):
                chunks.append(chunk)
                downloaded += len(chunk)
                if total > 0:
                    report(int(downloaded / total * 50), f"下载中... {downloaded//1024}KB")

            report(50, "下载完成，正在解压...")

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = os.path.join(tmpdir, "update.zip")
                with open(zip_path, "wb") as f:
                    for c in chunks:
                        f.write(c)

                report(60, "解压中...")
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(tmpdir)

                # 找解压后的目录
                dirs = [d for d in os.listdir(tmpdir) if os.path.isdir(os.path.join(tmpdir, d))]
                source = os.path.join(tmpdir, dirs[0]) if dirs else tmpdir

                app_dir = self._app_dir()

                # 备份
                report(70, "备份当前文件...")
                backup_dir = os.path.join(app_dir, "_backup")
                if os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir)
                os.makedirs(backup_dir)
                for fname in UPDATE_FILES:
                    fp = os.path.join(app_dir, fname)
                    if os.path.exists(fp):
                        shutil.copy2(fp, os.path.join(backup_dir, fname))

                # 替换
                report(85, "替换文件...")
                count = 0
                for fname in UPDATE_FILES:
                    src = os.path.join(source, fname)
                    dst = os.path.join(app_dir, fname)
                    if os.path.exists(src):
                        shutil.copy2(src, dst)
                        count += 1
                        self.log(f"[更新] 更新: {fname}")

                self.current_version = self.latest_version
                self.update_available = False
                report(100, f"更新完成，共更新 {count} 个文件")
                return True

        except Exception as e:
            self.log(f"[更新] 更新失败: {e}")
            return False

    def check_async(self, callback=None):
        def worker():
            ok, ver, log = self.check_update()
            if callback:
                callback(ok, ver, log)
        threading.Thread(target=worker, daemon=True).start()