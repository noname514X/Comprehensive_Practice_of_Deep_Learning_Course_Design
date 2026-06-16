# SmartCare 端到端智能客服系统

本项目根据《深度学习综合实训课程设计选题指南》选择 **题目 8：端到端智能客服系统** 完成，场景设定为“电商耳机售后客服”。系统支持知识库问答、意图识别、模拟工具调用、多轮记忆、情绪安抚、转人工、Web 聊天界面、历史记录持久化和测试评估。

## 选题理由

题目 8 不依赖 GPU，数据可以自建，适合小组在本地演示；同时覆盖课程中的 RAG、Prompt Engineering、Function Calling、Agent 路由、Memory、工程实践和评估方法。相比单纯命令行实验，本项目提供 Web 界面、完整用户流程和 SQLite 历史记录，符合指南中的产品完整性加分项。

## 核心功能

- RAG 知识库问答：导入 FAQ 和产品/售后文档，基于 TF-IDF 检索 Top-K 片段，并在回答中展示引用来源。
- 意图识别：识别订单查询、退换货、产品咨询、保修、投诉、闲聊、转人工和兜底场景。
- Function Calling：模拟 `query_order`、`create_ticket`、`transfer_human`、`compare_products` 四类工具。
- 多轮记忆：使用 SQLite 记录对话历史和会话状态，例如最近订单号、最近咨询产品、待补充意图。
- 情绪识别：检测投诉、强烈负面情绪，并触发高优先级人工转接策略。
- Web 界面：提供客服聊天窗口、演示场景按钮、工具调用面板、引用来源面板和运行统计。
- 评估脚本：提供 20 条测试对话和 RAG Top-K 消融实验，生成 Markdown 评估报告。

## 项目结构

```text
smartcare_customer_service/
├── app.py
├── run_evaluation.py
├── run_rag_ablation.py
├── customer_service/
│   ├── chatbot.py
│   ├── intent.py
│   ├── knowledge_base.py
│   ├── llm.py
│   ├── memory.py
│   ├── models.py
│   ├── tools.py
│   ├── vector_store.py
│   └── web.py
├── data/
│   ├── orders.json
│   ├── evaluation/
│   └── knowledge/
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── reports/
│   ├── course_report.md
│   ├── defense_script.md
│   ├── predicted_questions.md
│   ├── evaluation_results.md
│   ├── rag_ablation.md
│   ├── ppt_outline.md
│   └── vibe_coding_log.md
└── runtime/
```

## 运行方式

进入项目目录：

```bash
cd smartcare_customer_service
```

启动 Web 应用：

```bash
python3 app.py --port 8000
```

浏览器访问：

```text
http://127.0.0.1:8000
```

如 8000 端口被占用，可换成其他端口：

```bash
python3 app.py --port 8010
```

## 可选 Ollama 调用

默认模式不依赖大模型，会用可解释的检索模板生成回答，保证演示稳定。如果本机已安装 Ollama，可以启用 Qwen2.5：

```bash
ollama pull qwen2.5:1.5b
USE_OLLAMA=1 OLLAMA_MODEL=qwen2.5:1.5b python3 app.py --port 8000
```

## 演示问题

- `订单号 2024060112345 到哪了？`
- `订单 2024060112345 的 XX 耳机左耳没声音，我想换货`
- `XX 耳机防水吗？能戴着游泳吗？`
- `XX 和 YY 两款耳机有什么区别？`
- `你们这什么破服务，再不处理我就投诉了！`
- `我要人工客服`

## 评估方式

运行 20 条测试对话评估：

```bash
python3 run_evaluation.py
```

运行 RAG Top-K 消融实验：

```bash
python3 run_rag_ablation.py
```

当前结果：

- 20 条测试样本意图识别准确率：100.0%
- 工具调用正确率：100.0%
- RAG 引用命中率：100.0%
- RAG 检索 Top-1 命中率：87.5%
- RAG 检索 Top-3 命中率：100.0%

## 三人分工

| 成员 | 主要职责 | 答辩讲解部分 |
| --- | --- | --- |
| 成员 A | 选题分析、知识库构建、RAG 检索、意图识别、Agent 路由 | 项目背景、系统架构、RAG 检索、意图路由 |
| 成员 B | Function Calling、SQLite 记忆、Web 界面、功能演示 | 工具调用、记忆系统、Web 演示 |
| 成员 C | 评估脚本、消融实验、实验分析、总结改进 | 实验评估、结果分析、未来展望 |

## 提交材料

- 源代码：`customer_service/`、`static/`、`app.py`
- 数据：`data/knowledge/`、`data/orders.json`、`data/evaluation/`
- README：`README.md`
- 课程设计报告：`reports/course_report.md`
- 答辩材料：`reports/defense_script.md`、`reports/predicted_questions.md`、`reports/ppt_outline.md`
- 实验报告：`reports/evaluation_results.md`、`reports/rag_ablation.md`
- Vibe Coding 记录：`reports/vibe_coding_log.md`
