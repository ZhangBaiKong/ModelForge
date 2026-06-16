#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模型整合 (ModelForge) - 入口"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import ModelForgeApp

if __name__ == "__main__":
    app = ModelForgeApp()
    app.run()