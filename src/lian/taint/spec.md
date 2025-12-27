# SFG 污点与依赖分析技术规范 (V4.1 最终冻结版)

## 1. 核心哲学：分层精度模型 (Layered Precision)

本规范采用“双轨制”传播模型，旨在解决复杂工程环境下数据流的**连续性**与**可解释性**：

* **物理轨 (STATE)**：负责物理值级别的精确跟踪，提供高置信度的漏洞证据。
* **语义轨 (SYMBOL)**：负责逻辑实体层面的容错传播，作为物理轨断裂时的语义续接。
* **放大器 (STMT)**：作为语义逻辑的泵，根据指令类型决定污染在双轨间的双向流动。

---

## 2. 污点强度与管理模型 (Management Model)

### 2.1 污点强度定义

* **STATE_TAINT**：精确级。物理值被明确污染。
* **SYMBOL_TAINT**：语义级。符号逻辑不可信，可独立于 State 存在。
* **STMT_TAINT**：触发级。指令成为污染传播媒介。

### 2.2 全局污点池 (Taint Pools)

1. **Taint_State_Pool**: `Map<StateID, Set<SourceID>>`
2. **Taint_Symbol_Pool**: `Map<SymbolID, Set<SourceID>>`（独立存储，支持 Symbol-only 状态）
3. **Evidence_Journal**: `Map<NodeID, List<StepRecord>>`

---

## 3. 核心传播规则 (Unified Dispatch Rules)

### Rule L2-1: State → Symbol (向上提升)

* **触发**：State 被污染。
* **动作**：其所属 Symbol 自动标记为 `SYMBOL_TAINT`。

### Rule L2-2: Symbol → Symbol (语义平移)

* **触发**：`Sym_A` 为脏，且存在 `Sym_A --SYMBOL_FLOW--> Sym_B`。
* **动作**：`Sym_B` 直接标记为 `SYMBOL_TAINT`，跳过 State 校验。**这是解决断链的核心机制。**

### Rule L2-3: Stmt-Mediated Propagation (逻辑放大)

* **触发**：Stmt 引用了脏 Symbol 或脏 State。
* **动作**：根据 Stmt 类型规则，标记其 Def 的 Symbol/State 为脏。支持自定义规则（如：，若  脏，则  脏）。

### Rule L2-4: Symbol → State (物理回流 - 选做)

* **触发**：Symbol 脏且进入了新的赋值点。
* **动作**：将污染同步给新生成的 State，重新激活物理轨精确分析。

---

## 4. 分析模式与收敛约束 (Mode & Convergence)

### 4.1 模式矩阵

| 特性 | **Strict Taint** | **Engineering Taint** | **Dependency Slicing** |
| --- | --- | --- | --- |
| **主导轨道** | 物理轨 (State) | **双轨 (State + Symbol)** | 双轨逆向 |
| **断链处理** | 停止分析 | **Symbol 语义续接** | 语义续接 |
| **精度级别** | 高 (Confirmed) | 中 (Heuristic) | - |

### 4.2 语义收敛约束 (The Convergence Boundary)

* **弱证据标记**：若污点通过 `SYMBOL_FLOW` 连续传递超过  级且始终无法回流至物理 `STATE`，该传播链应在 Evidence 中标记为 `Weak Evidence`。
* **降权机制**：在结果输出阶段，仅包含 `SYMBOL_TAINT` 的路径优先级应低于包含 `STATE_TAINT` 的路径。

---

## 5. 跨函数与路径重构 (Context & Trace)

* **Context-Tagging**：Symbol 污染状态必须与当前 `ContextID` 绑定。
* **Path Reconstruction**：基于 `Evidence_Journal` 的前驱指针，逆向提取包含 `STATE_COPY`、`SYMBOL_FLOW` 以及 `STMT` 触发点的全量证据序列。

---

## 6. 冻结声明 (Final Freeze - V4.1)

> **本规范于 2025-12-26 正式发布并冻结。**
> 核心价值：通过解耦物理载体与语义载体，实现了在不完整代码库上依然稳健的污点分析能力。
