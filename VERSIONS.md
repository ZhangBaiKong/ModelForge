# ModelForge 版本历史

## 版本命名规则
v主版本.次版本.修订版本.构建号
例：v0.0.1.1-betaA

text

- **主版本**：大重构、架构变更
- **次版本**：新功能
- **修订版本**：Bug修复
- **构建号**：小改动、打包更新
- **后缀**：beta（测试）、alpha（早期测试）、正式版不加后缀

## 版本记录

### v0.0.1.1-betaA (2026-06-18)
- Markdown渲染（代码块、标题、列表、粗体高亮）
- 复制按钮（一键复制AI回复）
- 停止生成（发送后可中途取消）
- 模型方向扩展：9个方向+多选+提示词自动合并
- 角色选择移入模型设置
- 对话布局：AI左、用户右
- 文件分类整理
- 版本管理规范

### v0.0.1.0 (2026-06-17)
- 初版发布
- 基础框架、编排引擎
- 多对话管理
- 图片附件支持
- 热更新框架
- 安装包支持

## 如何回退版本

### 方法1：查看所有版本标签
```bash
git tag -l

- **主版本**：大重构、架构变更
- **次版本**：新功能
- **修订版本**：Bug修复
- **构建号**：小改动、打包更新
- **后缀**：beta（测试）、alpha（早期测试）、正式版不加后缀

## 版本记录

### v0.0.1.1-betaA (2026-06-18)
- Markdown渲染（代码块、标题、列表、粗体高亮）
- 复制按钮（一键复制AI回复）
- 停止生成（发送后可中途取消）
- 模型方向扩展：9个方向+多选+提示词自动合并
- 角色选择移入模型设置
- 对话布局：AI左、用户右
- 文件分类整理
- 版本管理规范

### v0.0.1.0 (2026-06-17)
- 初版发布
- 基础框架、编排引擎
- 多对话管理
- 图片附件支持
- 热更新框架
- 安装包支持

## 如何回退版本

### 方法1：查看所有版本标签
```bash
git tag -l

方法2：回退到某个版本
bash
git checkout v0.0.1.0
git checkout v0.0.1.0

方法3：回退后创建新分支
bash
git checkout -b restore-branch v0.0.1.0
git checkout -b restore-branch v0.0.1.0

方法4：查看版本差异
bash
git diff v0.0.1.0..v0.0.1.1-betaA
git diff v0.0.1.0..v0.0.1.1-betaA

方法5：撤销某个版本的更改（保留历史）
bash
git revert <commit-hash>
git revert <commit-hash>
text

---

## 第6步：Git版本标签

打开cmd，依次执行：

---

## 第6步：Git版本标签

打开cmd，依次执行：
cd /d E:\wodeAI\ModelForge

git add -A

git commit -m "v0.0.1.1-betaA - Markdown渲染、复制按钮、停止生成、方向多选、文件分类"

git tag -a v0.0.1.0 -m "初版：基础框架、编排引擎、多对话管理"

git tag -a v0.0.1.1-betaA -m "betaA：Markdown、复制、停止、方向多选、文件分类"

git branch -M main

git push -u origin main --force

git push origin --tags