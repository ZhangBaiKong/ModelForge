#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编排引擎 (Orchestrator Engine) v3
修复：7B模型JSON模板抄写问题、用示例教小模型、更健壮的解析
"""

import json
import os
import re
import base64
import requests


class APIClient:
    """统一的 API 客户端，兼容所有 OpenAI 格式的接口"""

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
    """编排调度器"""

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

    def _is_vision_model(self, model_cfg):
        if not model_cfg:
            return False
        direction = model_cfg.get("direction", "")
        model_id = model_cfg.get("model_name", "").lower()
        if "图片识别" in direction or "Vision" in direction:
            return True
        if any(kw in model_id for kw in ["vl", "vision", "visual"]):
            return True
        return False

    def _encode_image_base64(self, image_path):
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lstrip(".").lower()
        mime_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "gif": "image/gif",
            "webp": "image/webp", "bmp": "image/bmp",
        }
        mime = mime_map.get(ext, "image/jpeg")
        return b64, mime

    def _describe_image(self, model_cfg, image_path):
        b64, mime = self._encode_image_base64(image_path)
        client = self._build_client(model_cfg)
        msgs = [
            {
                "role": "system",
                "content": model_cfg.get(
                    "system_prompt",
                    "请详细描述这张图片的内容，包括文字、布局、颜色、物体等。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                    {"type": "text", "text": "请详细描述这张图片。"},
                ],
            },
        ]
        return client.chat(msgs)

    def _build_system_prompt(self):
        """用示例教小模型，而不是给模板"""
        main = self.cfg.get_main_model() or {}
        subs = self.cfg.get_sub_models()

        sub_desc = ""
        for s in subs:
            sub_desc += f'\n- {s.get("id","")} ({s["name"]}): {s["direction"]}'
        if not sub_desc:
            sub_desc = "\n（暂无副模型）"

        base = main.get("system_prompt", "")

        return f"""{base}

===== 任务调度规则 =====
你可以使用的副模型：{sub_desc}

规则很简单：
1. 如果你能独立完成，直接回答，不要输出JSON
2. 如果需要副模型帮助，输出一个纯JSON，格式如下：
{{"orchestrate":true,"tasks":[{{"target":"副模型id","instruction":"具体要做什么","data":"具体数据"}}],"self_tasks":"你自己要做的具体事情"}}

重要：JSON中每个字段都必须填入真实、具体的内容。不要抄写模板。

示例1 - 不需要副模型：
用户：写一个hello world程序
你的回答：print("hello world")

示例2 - 需要副模型帮助：
用户：请识别这张图片中的文字，然后翻译成英文
你的回答：
{{"orchestrate":true,"tasks":[{{"target":"sub_0","instruction":"请识别图片中的所有文字，逐字输出","data":"图片已附上"}}],"self_tasks":"将识别出的文字翻译成英文"}}

示例3 - 多个副模型：
用户：根据这张图片画一个类似界面，再写后端代码
你的回答：
{{"orchestrate":true,"tasks":[{{"target":"sub_0","instruction":"描述图片中的界面布局、颜色、组件位置","data":"图片已附上"}}],"self_tasks":"根据界面描述编写前端代码和后端代码"}}

记住：只输出JSON或直接回答，不要两种都输出。不要用```包裹JSON。"""

    # ---------- JSON解析（超强版） ----------

    def _parse_orchestration(self, text):
        """从回复中提取编排JSON，多重策略"""
        text = text.strip()

        # 策略1：去掉markdown包裹
        cleaned = text
        if "```" in cleaned:
            match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()

        # 策略2：直接解析
        try:
            obj = json.loads(cleaned)
            if isinstance(obj, dict) and obj.get("orchestrate"):
                return self._validate_orchestration(obj)
        except json.JSONDecodeError:
            pass

        # 策略3：逐段搜索JSON
        for start in range(len(cleaned)):
            if cleaned[start] == "{":
                # 找到对应的右花括号
                depth = 0
                in_string = False
                escape = False
                for end in range(start, len(cleaned)):
                    c = cleaned[end]
                    if escape:
                        escape = False
                        continue
                    if c == '\\' and in_string:
                        escape = True
                        continue
                    if c == '"' and not escape:
                        in_string = not in_string
                        continue
                    if not in_string:
                        if c == '{':
                            depth += 1
                        elif c == '}':
                            depth -= 1
                            if depth == 0:
                                candidate = cleaned[start:end + 1]
                                try:
                                    obj = json.loads(candidate)
                                    if isinstance(obj, dict) and obj.get("orchestrate"):
                                        return self._validate_orchestration(obj)
                                except json.JSONDecodeError:
                                    pass
                                break

        # 策略4：正则暴力提取
        pattern = r'\{[^{}]*"orchestrate"\s*:\s*true[^{}]*\}'
        match = re.search(pattern, cleaned)
        if match:
            try:
                obj = json.loads(match.group())
                if isinstance(obj, dict) and obj.get("orchestrate"):
                    return self._validate_orchestration(obj)
            except json.JSONDecodeError:
                pass

        return None

    def _validate_orchestration(self, obj):
        """
        验证编排JSON质量。
        如果tasks里的instruction或data是模板占位符，说明模型没真正理解，拒绝编排。
        """
        PLACEHOLDER_PHRASES = [
            "为副模型翻译的精确指令",
            "传递给副模型的数据",
            "精确指令",
            "具体指令",
            "具体数据",
        ]

        tasks = obj.get("tasks", [])
        has_placeholder = False

        for task in tasks:
            inst = task.get("instruction", "")
            data = task.get("data", "")
            for phrase in PLACEHOLDER_PHRASES:
                if phrase in inst or phrase in data:
                    has_placeholder = True
                    break
            if not task.get("target", "").strip():
                has_placeholder = True

        if has_placeholder:
            self.log("[编排] 检测到模板占位符，模型未真正理解编排，跳过编排")
            return None

        # 修复 self_tasks 位置错误
        self_tasks = obj.get("self_tasks", "")
        fixed_tasks = []
        for task in tasks:
            if isinstance(task, dict):
                if "self_tasks" in task and not self_tasks:
                    self_tasks = task.pop("self_tasks")
                if task.get("target", "").strip():
                    fixed_tasks.append(task)
        obj["tasks"] = fixed_tasks
        obj["self_tasks"] = self_tasks

        if not fixed_tasks and not self_tasks:
            return None

        return obj

    # ---------- 主处理流程 ----------

    def process(self, user_message, images=None, history=None):
        self.log("[编排] 收到用户请求")

        main_cfg = self.cfg.get_main_model()
        if not main_cfg:
            return "请先在右侧配置主模型"

        main_client = self._build_client(main_cfg)
        main_is_vision = self._is_vision_model(main_cfg)

        # ---- 1. 图片处理 ----
        image_context = ""
        if images and not main_is_vision:
            img_model = self._find_sub_by_direction("图片识别")
            if img_model:
                for p in images:
                    self.log(f"[识图] 发送给 {img_model['name']}...")
                    try:
                        desc = self._describe_image(img_model, p)
                        fname = os.path.basename(p)
                        image_context += f"\n[{fname}]: {desc}"
                        self.log("[识图] 完成")
                    except Exception as e:
                        self.log(f"[识图] 失败: {e}")
                        fname = os.path.basename(p)
                        image_context += f"\n[{fname}: 识别失败]"
            else:
                for p in images:
                    image_context += f"\n[{os.path.basename(p)}]"

        # ---- 2. 构建消息 ----
        sys_prompt = self._build_system_prompt()
        msgs = [{"role": "system", "content": sys_prompt}]
        if history:
            msgs.extend(history)

        if images and main_is_vision:
            self.log("[编排] 主模型支持视觉，图片直接发送")
            content_parts = []
            for p in images:
                b64, mime = self._encode_image_base64(p)
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                })
            content_parts.append({
                "type": "text",
                "text": user_message,
            })
            msgs.append({"role": "user", "content": content_parts})
        else:
            context = user_message
            if image_context:
                context += "\n\n图片信息:" + image_context
            msgs.append({"role": "user", "content": context})

        # ---- 3. 调用主模型 ----
        self.log("[主模型] 分析任务中...")
        try:
            main_resp = main_client.chat(msgs)
        except Exception as e:
            self.log(f"[主模型] 调用失败: {e}")
            return f"主模型调用失败: {e}"

        self.log("[主模型] 收到响应")

        # ---- 4. 尝试解析编排 ----
        orch = self._parse_orchestration(main_resp)
        if not orch:
            self.log("[编排] 主模型独立完成")
            return main_resp

        tasks = orch.get("tasks", [])
        self_tasks = orch.get("self_tasks", "")
        self.log(f"[编排] 拆解为 {len(tasks)} 个子任务")
        if self_tasks:
            self.log(f"[编排] 主模型自己执行: {self_tasks[:60]}...")

        # ---- 5. 执行副模型任务 ----
        results = {}
        for task in tasks:
            tid = task.get("target", "")
            inst = task.get("instruction", "")
            data = task.get("data", "")
            self.log(f"[副模型] 调用 {tid}: {inst[:50]}...")

            sub_cfg = None
            for s in self.cfg.get_sub_models():
                if s.get("id") == tid:
                    sub_cfg = s
                    break

            if not sub_cfg:
                self.log(f"[错误] 副模型 {tid} 未配置")
                results[tid] = f"[未找到副模型: {tid}]"
                continue

            sub_client = self._build_client(sub_cfg)
            try:
                r = sub_client.chat([
                    {"role": "system", "content": inst},
                    {"role": "user", "content": data or user_message},
                ])
                results[tid] = r
                self.log(f"[副模型] {tid} 完成")
            except requests.exceptions.HTTPError as e:
                error_detail = ""
                if e.response is not None:
                    error_detail = e.response.text[:500]
                self.log(f"[副模型] {tid} 失败: {e}")
                self.log(f"[副模型] {tid} 错误详情: {error_detail}")
                results[tid] = f"[调用失败: {e}]"
            except Exception as e:
                self.log(f"[副模型] {tid} 失败: {e}")
                results[tid] = f"[调用失败: {e}]"

        # ---- 6. 整合结果 ----
        self.log("[编排] 整合所有结果...")

        summary_parts = ["各模型任务执行结果："]
        if self_tasks:
            summary_parts.append(f"\n[你自己的任务]\n{self_tasks}")
        for tid, r in results.items():
            summary_parts.append(f"\n[{tid} 的结果]\n{r}")

        summary = "\n".join(summary_parts)
        summary += "\n\n请根据以上所有结果，给用户一个完整、清晰的最终回答。"

        synth_msgs = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": main_resp},
            {"role": "user", "content": summary},
        ]
        try:
            final = main_client.chat(synth_msgs)
            self.log("[编排] 最终回答已生成")
            return final
        except Exception as e:
            self.log(f"[编排] 整合失败: {e}")
            fallback = ""
            if self_tasks:
                fallback += f"主模型执行:\n{self_tasks}\n\n"
            for tid, r in results.items():
                fallback += f"--- {tid} ---\n{r}\n\n"
            return fallback