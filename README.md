# Expert Distiller

<p align="center">
  <b>自适应专家访谈 Skill</b><br>
  <b>Adaptive Expert Interview Skill</b>
</p>

<p align="center">
  <a href="#">中文</a> | <a href="#english">English</a>
</p>

---

## 简介

**Expert Distiller** 是一个用于对领域专家进行自适应深度访谈的 AI Skill。通过多轮对话，自动生成从易到难、自适应调整的问题，挖掘专家的决策风格、思维模式和领域认知，最终输出标准化的问答对。

### 核心特性

- **🎯 自适应提问** — 根据回答动态调整问题方向和深度
- **📊 四阶段难度阶梯** — 破冰期 → 基础期 → 深入期 → 升华期
- **🔍 话题覆盖追踪** — 自动追踪 5 大维度覆盖情况
- **💡 智能追问** — 检测追问信号，自动深入挖掘
- **⏱️ 时长控制** — 超时自动切换快速模式，保证进度
- **🔄 中断恢复** — 支持从状态快照恢复访谈
- **🤖 通用 Agent 兼容** — 可在 Claude Code、OpenClaw 等任何 Agent 上运行

---

## 项目结构

```
expert-distiller/
├── SKILL.md                    # Agent 指令文档
├── interview_engine.py         # Python 核心引擎
├── prompts/
│   ├── generate_question.txt   # 问题生成 Prompt 模板
│   └── analyze_response.txt    # 回答分析 Prompt 模板
└── tests/                      # 测试套件 (43 tests)
```

### 核心模块

| 模块 | 职责 |
|------|------|
| `InterviewState` | 状态管理（JSON 持久化） |
| `PhaseController` | 四阶段状态机控制 |
| `TopicTracker` | 话题维度覆盖追踪 |
| `FollowUpController` | 追问规则与限制 |
| `OutputFormatter` | 输出格式化（JSON Lines、快照） |

---

## 快速开始

### 1. 初始化访谈

```bash
python interview_engine.py init \
  --domain "消费行业投资" \
  --expert "专注消费赛道15年的VC合伙人" \
  --target 50 \
  --keywords "品牌,渠道,消费品" \
  --output ./interview_state.json
```

### 2. 查看状态

```bash
python interview_engine.py status --state ./interview_state.json
```

### 3. 更新问答对

```bash
python interview_engine.py update \
  --state ./interview_state.json \
  --q-id 1 \
  --question "消费投资的核心原则是什么？" \
  --answer "品牌护城河最重要" \
  --analysis '{"dimension": "core_principles", "needs_follow_up": false, "quality": "high"}'
```

### 4. 导出结果

```bash
python interview_engine.py export \
  --state ./interview_state.json \
  --output ./interview_result.jsonl
```

---

## Agent 工作流程

Agent 读取 `SKILL.md` 后，按以下流程执行：

```
初始化 → 生成问题 → 获取回答 → 分析回答 → 更新状态 → 循环 → 导出
  ↑___________________________________________________________|
```

1. **初始化** — 收集领域、专家定位、目标数量
2. **生成问题** — 根据当前阶段和状态，通过 LLM 生成问题
3. **获取回答** — 向专家展示问题，获取回答
4. **分析回答** — LLM 分析回答质量，判断是否需要追问
5. **更新状态** — Python 引擎更新进度、话题覆盖、追问计数
6. **循环** — 重复直到达到目标数量
7. **导出** — 输出 JSON Lines 格式问答对

---

## 测试

```bash
python -m unittest discover tests -v
```

**43 tests, all passing ✅**

---

## 阶段设计

| 阶段 | 占比 | 问题类型 | 目的 |
|------|------|----------|------|
| 破冰期 | 10% | 选择题、判断题 | 帮助进入状态 |
| 基础期 | 30% | 简答题、定义题 | 获取基础知识 |
| 深入期 | 40% | 案例分析、情景题 | 挖掘决策框架 |
| 升华期 | 20% | 假设问题、边界问题 | 探索认知边界 |

---

## 输出格式

### JSON Lines

```jsonl
{"q_id": 1, "phase": "warmup", "type": "choice", "dimension": "core_principles", "question": "...", "answer": "...", "timestamp": "..."}
{"q_id": 2, "phase": "deep", "type": "case", "dimension": "typical_cases", "scenario": "...", "question": "...", "answer": "...", "timestamp": "..."}
```

### 状态快照（中断恢复）

```json
{
  "completed_q_ids": [1, 2, 3],
  "current_phase": "deep",
  "covered_topics": ["core_principles", "typical_cases"],
  "remaining_target": 47
}
```

---

## 设计原则

| 原则 | 说明 |
|------|------|
| **第0优先级** | 不中断访谈，永远推进对话 |
| **第1优先级** | 完成目标问答对数量 |
| **第2优先级** | 在承诺时间内完成 |
| **第3优先级** | 在时间允许的情况下深入追问 |

---

## 依赖

- Python 3.9+（仅标准库）

---

<hr id="english">

## Introduction

**Expert Distiller** is an AI Skill for conducting adaptive in-depth interviews with domain experts. Through multi-turn dialogue, it automatically generates progressively difficult questions, uncovers experts' decision-making styles, thinking patterns, and domain knowledge, ultimately producing standardized Q&A pairs.

### Key Features

- **🎯 Adaptive Questioning** — Dynamically adjusts question direction and depth based on responses
- **📊 Four-Phase Difficulty Ladder** — Warmup → Foundation → Deep → Advanced
- **🔍 Topic Coverage Tracking** — Automatically tracks coverage across 5 dimensions
- **💡 Smart Follow-ups** — Detects follow-up signals and digs deeper automatically
- **⏱️ Time Control** — Switches to fast mode when overtime to ensure progress
- **🔄 Resume Support** — Supports resuming interviews from state snapshots
- **🤖 Universal Agent Compatible** — Works on Claude Code, OpenClaw, and any Agent

---

## Project Structure

```
expert-distiller/
├── SKILL.md                    # Agent instruction document
├── interview_engine.py         # Python core engine
├── prompts/
│   ├── generate_question.txt   # Question generation prompt template
│   └── analyze_response.txt    # Response analysis prompt template
└── tests/                      # Test suite (43 tests)
```

### Core Modules

| Module | Responsibility |
|--------|---------------|
| `InterviewState` | State management (JSON persistence) |
| `PhaseController` | Four-phase state machine control |
| `TopicTracker` | Topic dimension coverage tracking |
| `FollowUpController` | Follow-up rules and limits |
| `OutputFormatter` | Output formatting (JSON Lines, snapshots) |

---

## Quick Start

### 1. Initialize Interview

```bash
python interview_engine.py init \
  --domain "Consumer Industry Investment" \
  --expert "VC partner with 15 years in consumer" \
  --target 50 \
  --keywords "brand,channel,consumer" \
  --output ./interview_state.json
```

### 2. Check Status

```bash
python interview_engine.py status --state ./interview_state.json
```

### 3. Update Q&A Pair

```bash
python interview_engine.py update \
  --state ./interview_state.json \
  --q-id 1 \
  --question "What is the core principle of consumer investment?" \
  --answer "Brand moat is the most important" \
  --analysis '{"dimension": "core_principles", "needs_follow_up": false, "quality": "high"}'
```

### 4. Export Results

```bash
python interview_engine.py export \
  --state ./interview_state.json \
  --output ./interview_result.jsonl
```

---

## Agent Workflow

After reading `SKILL.md`, the Agent executes the following workflow:

```
Initialize → Generate Question → Get Answer → Analyze → Update State → Loop → Export
     ↑_____________________________________________________________________________|
```

1. **Initialize** — Collect domain, expert position, target count
2. **Generate Question** — Generate questions via LLM based on current phase and state
3. **Get Answer** — Present question to expert, get response
4. **Analyze** — LLM analyzes response quality, determines if follow-up needed
5. **Update State** — Python engine updates progress, coverage, follow-up counts
6. **Loop** — Repeat until target count reached
7. **Export** — Output JSON Lines format Q&A pairs

---

## Testing

```bash
python -m unittest discover tests -v
```

**43 tests, all passing ✅**

---

## Phase Design

| Phase | Ratio | Question Types | Purpose |
|-------|-------|----------------|---------|
| Warmup | 10% | Choice, Judge | Get into the flow |
| Foundation | 30% | Open, Definition | Collect basic knowledge |
| Deep | 40% | Case, Scenario | Uncover decision frameworks |
| Advanced | 20% | Hypothetical, Boundary | Explore cognitive limits |

---

## Output Format

### JSON Lines

```jsonl
{"q_id": 1, "phase": "warmup", "type": "choice", "dimension": "core_principles", "question": "...", "answer": "...", "timestamp": "..."}
{"q_id": 2, "phase": "deep", "type": "case", "dimension": "typical_cases", "scenario": "...", "question": "...", "answer": "...", "timestamp": "..."}
```

### State Snapshot (Resume)

```json
{
  "completed_q_ids": [1, 2, 3],
  "current_phase": "deep",
  "covered_topics": ["core_principles", "typical_cases"],
  "remaining_target": 47
}
```

---

## Design Principles

| Priority | Principle |
|----------|-----------|
| **P0** | Never interrupt the interview, always move forward |
| **P1** | Complete the target number of Q&A pairs |
| **P2** | Finish within the promised time |
| **P3** | Dig deeper when time allows |

---

## Dependencies

- Python 3.9+ (standard library only)

---

## License

MIT
