# SFG 污点与依赖分析技术规范 (V2.0 终极完整版)

## 1. 导言与核心哲学 (Introduction & Philosophy)

### 1.1 目的

本规范旨在定义一套在状态流图（State Flow Graph, SFG）上进行数据流分析的标准协议。通过显式区分符号（Symbol）、状态（State）与语句（Stmt），解决静态分析中路径敏感性与语义漂移的问题。

### 1.2 核心原则

* **Symbol-State 二元论**：Symbol 是静态的“名”，State 是动态的“值”。所有的污染都在值上，所有的关联都在名上。
* **Layered Decoupling**：将“图怎么走（拓扑）”与“走的时候发生什么（语义）”严格分离。
* **Existential Taint (一滴血原则)**：Symbol 的污染状态取决于其关联 State 集合的并集结果。

---

## 2. 节点与边缘定义详解 (Detailed Graph Ontology)

### 2.1 节点种类 (SFG_NODE_KIND)

1. **REGULAR (0)**：结构性节点，用于组织图结构，不参与数据流语义。
2. **STMT (1)**：程序点。它是数据流的触发源或汇聚点。属性包含：源代码行号、指令类型（Assign, Call, Return等）。
3. **SYMBOL (2)**：程序的抽象实体。包括：
* `VariableSymbol`: 局部或全局变量。
* `FieldSymbol`: 对象的属性。
* `ParameterSymbol`: 函数参数。


4. **STATE (3)**：Symbol 在特定时间点的抽象值。它是 Taint 的唯一承载者。

### 2.2 边缘种类 (SFG_EDGE_KIND)

* **SYMBOL_STATE (5)**：核心绑定边。连接 Symbol 与其产生的多个 State。
* **SYMBOL_FLOW (3)**：符号级传播，代表代码层面的赋值（）或传参。
* **STATE_COPY (10)**：底层值拷贝，代表 IR 级的数据移动。
* **STATE_INCLUSION (7)**：容器包含关系，如  产生的状态依赖。
* **CALL_RETURN (9)**：跨函数流转边，连接调用方实参与被调用方形参，以及返回值。
* **SYMBOL_IS_DEFINED (1)** / **SYMBOL_IS_USED (2)**：建立 Stmt 与数据实体的证据关联。

---

## 3. 统一分析引擎算法 (Unified Analysis Engine)

### 3.1 传播状态维护 (Analysis State)

* **TaintDomain**: 维护一个全局映射 。
* **Worklist**: 存储当前待扩散的节点（State 或 Symbol）。
* **Visited**: 记录已处理的 `(Node, Context)` 对，防止环路。

### 3.2 两层分发机制 (The Dual-Layer Dispatch)

#### Layer 1: 拓扑遍历 (Topology Layer)

负责根据 `Direction` (Forward/Backward) 处理图的连通性。如果边类型在 `EdgeFilter` 中，则将 `TargetNode` 放入 Worklist。

#### Layer 2: 语义调度 (Semantic Layer - Event Driven)

必须严格执行以下四项逻辑闭合规则：

1. **Rule S-Mark (State to Symbol)**:
当 `State s` 被标记污染时，自动标记其上级 `Symbol` 为派生污染（Derived Tainted）。
2. **Rule S-Flow (Symbol to State)**:
当处理 `State s` 且其属于 `Sym_A`，若存在 `Sym_A --SYMBOL_FLOW--> Sym_B`，则将污染扩散至 `Sym_B` 关联的所有 `State`。
3. **Rule S-Inclusion (Object Context)**:
当 `State_Field` 被污染，其所属的 `State_Object` 标记为“部分污染”。在 AGGRESSIVE 模式下，这种污染会扩散至整个对象。
4. **Rule S-Evidence (Evidence Hook)**:
* **Forward**: 记录所有 `USE` 了污染节点的 `STMT`。
* **Backward**: 记录所有 `DEFINE` 了依赖节点的 `STMT`。

---

## 4. 分析模式与敏感度 (Analysis Modes & Sensitivity)

### 4.1 模式矩阵 (Standard Matrix)

| 维度 | Taint Tracking | Influence Analysis | Dependency Slicing |
| --- | --- | --- | --- |
| **种子 (Seeds)** | Source States | Source Symbols | Sink Symbols |
| **方向 (Dir)** | Forward | Forward | **Backward** |
| **判定逻辑** | Sink Symbol 关联 State 集合非空 | 遍历达到的 Symbol 闭包 | 溯源达到的所有节点 |
| **边缘策略** | STRICT/CONSERVATIVE | AGGRESSIVE | Dependency Set |

### 4.2 精度开关 (Edge Filters)

* **STRICT**: 仅 `STATE_COPY`, `SYMBOL_FLOW`, `CALL_RETURN`。
* **CONSERVATIVE**: 增加 `STATE_INCLUSION`（处理字段污染）。
* **AGGRESSIVE**: 增加所有 `INDIRECT_*` 边（处理指针、别名、隐式流）。

---

## 5. 跨函数与上下文处理 (Inter-procedural Logic)

### 5.1 上下文敏感性 (Context Sensitivity)

为了防止分析在调用栈间“串门”：

1. 每个 `STATE` 在进入函数时挂载 `ContextID`。
2. `CALL_RETURN` 边进行匹配校验：只有当前 `ContextStack` 的栈顶与返回点匹配时，数据流才有效。

### 5.2 递归处理

遇到递归调用时，采用 **Fixed-point (不动点)** 迭代，当 `State` 的属性不再发生变化时停止扩散。

---

## 6. 证据与路径重构 (Evidence Reconstruction)

### 6.1 证据链生成

系统不直接存储路径（防止路径爆炸），而是存储“前驱步记录”：
`Predecessor[CurrentNode] = (PrevNode, Stmt, EdgeKind)`

### 6.2 最终报告生成

当 Sink 被触发时，通过递归回溯 `Predecessor` 表，还原出完整的 `STMT` 序列，并按照程序执行顺序（Top-down）进行重排。

---

## 7. 边界情况处理 (Edge Cases)

* **Empty Definitions**: 若 `SYMBOL_IS_DEFINED` 发生但未产生新 `STATE`，传播在此路径挂起，等待下一个有效赋值。
* **Multiple In-edges**: 当一个 `STATE` 收到来自多个 Source 的污染时，取 SourceID 的**并集**，实现多源追溯。
* **Constant Folding**: 如果 `STATE` 代表一个已知常量且非污染，即使其 Symbol 被标记，该特定路径也可被修剪（Pruning）。

---

## 8. 冻结声明 (Final Freeze)

> **本规范 V2.0 终极版于 2025-12-26 正式发布并冻结。**
> 本规范涵盖了从底层拓扑到高层语义的所有必要约束，是 SFG 分析引擎开发的最高指导文件。
