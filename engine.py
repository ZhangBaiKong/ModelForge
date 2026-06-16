#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编排引擎"""

import json
import os
import base64
import requests


class APIClient:
    def __init__(self, api_url, api_key, model_name,
                 temperature=0.7, max_tokens=4096):
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, messages):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        resp = requests.post(
            self.api_url, headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


class Orchestrator:
    def __init__(self, config_manager, log_callback=None):
        self.cfg = config_manager
        self.log = log_callback or print

    def _build_client(self, model_cfg):
        if not model_cfg:
            return None
        return APIClient(
            model_cfg["api_url"],
            model_cfg["api_key"],
            model_cfg["model_name"],
            model_cfg.get("temperature", 0.7),
            model_cfg.get("max_tokens", 4096),
        )

    def _find_sub_by_direction(self, direction):
        for sub in self.cfg.get_sub_models():
            dirs = sub.get("direction", "")
            if direction in dirs:
                return sub
        return None

    def _build_system_prompt(self):
        main = self.cfg.get_main_model() or {}
        subs = self.cfg.get_sub_models()

        sub_desc = ""
        for s in subs:
            sub_desc += f'\n- {s.get("id","")} ({s["name"]}): 能力 - {s["direction"]}'
        if not sub_desc:
            sub_desc = "\n（暂无副模型）"

        base = main.get("system_prompt", "")

        return f"""{base}

===== 编排系统 =====
你是AI协作系统的核心调度模型。可用副模型：{sub_desc}

当任务需要其他模型协助时，严格输出以下JSON（不要加markdown标记）：
{{"orchestrate":true,"tasks":[{{"target":"副模型id","instruction":"精确指令","data":"传递数据"}}],"self_tasks":"你自己的部分"}}

能独立完成时直接回答，不输出JSON。
规则：为副模型量身翻译指令，不要原封不动转发用户输入。"""

    def _describe_image(self, model_cfg, image_path):
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lstrip(".").lower()
        mime_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "gif": "image/gif", "webp": "image/webp",
        }
        mime = mime_map.get(ext, "image/jpeg")

        client = self._build_client(model_cfg)
        msgs = [
            {
                "role": "system",
                "content": model_cfg.get(
                    "system_prompt", "请详细描述这张图片的内容"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                    {
                        "type": "text",
                        "text": "请详细描述图片内容，包括文字、布局、颜色等。",
                    },
                ],
            },
        ]
        return client.chat(msgs)

    def _parse_orchestration(self, text):
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            end_idx = -1 if lines[-1].strip().startswith("```") else len(lines)
            text = "\n".join(lines[1:end_idx])

        for start in range(len(text)):
            if text[start] == "{":
                for end in range(len(text), start, -1):
                    try:
                        obj = json.loads(text[start:end])
                        if isinstance(obj, dict) and obj.get("orchestrate"):
                            return obj
                    except json.JSONDecodeError:
                        continue
        return None

    def process(self, user_message, images=None, history=None):
        self.log("[编排] 收到用户请求")

        main_cfg = self.cfg.get_main_model()
        if not main_cfg:
            return "请先在右侧配置主模型"

        main_client = self._build_client(main_cfg)

        image_notes = []
        if images:
            img_model = self._find_sub_by_direction("图片识别")
            for p in images:
                if img_model:
                    self.log(f"[识图] 发送给 {img_model['name']}...")
                    try:
                        desc = self._describe_image(img_model, p)
                        image_notes.append(
                            f"[{os.path.basename(p)}]: {desc}"
                        )
                        self.log("[识图] 完成")
                    except Exception as e:
                        self.log(f"[识图] 失败: {e}")
                        image_notes.append(
                            f"[{os.path.basename(p)}: 识别失败]"
                        )
                else:
                    image_notes.append(f"[{os.path.basename(p)}]")

        context = user_message
        if image_notes:
            context += "\n\n图片信息:\n" + "\n".join(image_notes)

        sys_prompt = self._build_system_prompt()
        msgs = [{"role": "system", "content": sys_prompt}]
        if history:
            msgs.extend(history)
        msgs.append({"role": "user", "content": context})

        self.log("[主模型] 分析任务中...")
        try:
            main_resp = main_client.chat(msgs)
        except Exception as e:
            self.log(f"[主模型] 调用失败: {e}")
            return f"主模型调用失败: {e}"

        self.log("[主模型] 收到响应")

        orch = self._parse_orchestration(main_resp)
        if not orch:
            self.log("[编排] 主模型独立完成")
            return main_resp

        tasks = orch.get("tasks", [])
        self.log(f"[编排] 拆解为 {len(tasks)} 个子任务")

        results = {}
        for task in tasks:
            tid = task.get("target", "")
            inst = task.get("instruction", "")
            data = task.get("data", "")
            self.log(f"[副模型] 调用 {tid}: {inst[:40]}...")

            sub_cfg = None
            for s in self.cfg.get_sub_models():
                if s.get("id") == tid:
                    sub_cfg = s
                    break

            if not sub_cfg:
                self.log(f"[错误] 副模型 {tid} 未配置")
                results[tid] = f"[未找到 {tid}]"
                continue

            sub_client = self._build_client(sub_cfg)
            try:
                r = sub_client.chat(
                    [
                        {"role": "system", "content": inst},
                        {"role": "user", "content": data or context},
                    ]
                )
                results[tid] = r
                self.log(f"[副模型] {tid} 完成")
            except Exception as e:
                self.log(f"[副模型] {tid} 失败: {e}")
                results[tid] = f"[错误: {e}]"

        self.log("[编排] 整合结果...")
        self_tasks = orch.get("self_tasks", "")
        summary = "任务分配结果:\n"
        if self_tasks:
            summary += f"\n你自己执行: {self_tasks}\n"
        for tid, r in results.items():
            summary += f"\n--- {tid} ---\n{r}\n"

        summary += "\n请根据以上结果，给用户完整的最终回答。"

        synth_msgs = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": main_resp},
            {"role": "user", "content": summary},
        ]
        try:
            final = main_client.chat(synth_msgs)
            self.log("[编排] 最终结果已生成")
            return final
        except Exception as e:
            self.log(f"[编排] 整合失败: {e}")
            fallback = f"主模型分析: {self_tasks}\n\n"
            for tid, r in results.items():
                fallback += f"--- {tid} ---\n{r}\n\n"
            return fallback