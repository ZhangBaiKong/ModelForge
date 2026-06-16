#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配置管理器"""

import json
import os


class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self.load()

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return self.default_config()

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def default_config(self):
        return {
            "language": "zh",
            "theme": "dark",
            "storage_path": "./conversations",
            "models": {"main": None, "sub": []},
        }

    def get_main_model(self):
        return self.config["models"].get("main")

    def get_sub_models(self):
        return self.config["models"].get("sub", [])

    def set_main_model(self, model_cfg):
        self.config["models"]["main"] = model_cfg
        self.save()

    def add_sub_model(self, model_cfg):
        self.config["models"]["sub"].append(model_cfg)
        self.save()

    def update_sub_model(self, index, model_cfg):
        subs = self.config["models"]["sub"]
        if 0 <= index < len(subs):
            subs[index] = model_cfg
            self.save()

    def remove_sub_model(self, index):
        subs = self.config["models"]["sub"]
        if 0 <= index < len(subs):
            subs.pop(index)
            self.save()

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()