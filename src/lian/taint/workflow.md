# SFG 污点分析执行 Workflow

## Phase 0: 初始化 (Initialization)

1. **模式选择**：设置分析敏感度。
* `EngineeringTaint`: 开启双轨制，信用分初始 100。
* `StrictTaint`: 关闭 `L2-2` (Symbol Flow)，仅限物理轨。


2. **种子注入**：
* 将 `Source_State` 存入 `Taint_State_Pool`。
* 将 `Source_Symbol` 存入 `Taint_Symbol_Pool`。


3. **任务启动**：
* `Worklist = [Initial_Nodes]`
* `Visited = { (Node, ContextID, SourceID) }`



---

## Phase 1 & 2: 核心迭代与双轨调度 (The Core Dispatcher)

这是引擎的心脏。它不只是遍历图，而是通过状态变化驱动语义。

```python
while Worklist not empty:
    curr = Worklist.pop()
    
    # --- 拓扑传播 (Layer 1) ---
    for edge in SFG.out_edges(curr, Filter):
        target = edge.target
        if is_new_taint(target, context):
            process_new_taint(target, edge)

```

### 核心调度规则 (Layer 2 Rules)

#### Rule L2-1 & L2-2: 状态平移与续接

* **Case: State 变脏**  调用 `OnNewTaint(owner_symbol)`。
* **Case: Symbol 变脏**  激活 `SYMBOL_FLOW`。
* 沿着 `SYMBOL_FLOW` 边寻找 `Target_Symbol`。
* **信用分操作**：`target_score = current_score - 20` (语义续接扣分)。
* **动作**：标记 `Target_Symbol`，存入证据链，入队。



#### Rule L2-3: Stmt 订阅者激活 (The Amplifier)

**关键逻辑**：Stmt 不在 Worklist 中，它是被动的“订阅者”。

* **触发**：当 `OnNewTaint(node)` 发生。
* **动作**：
1. 查询 `SFG.get_used_by_stmts(node)` 找到所有引用该节点的语句。
2. 对每个 `Stmt` 应用建模逻辑（例如：`Assign`, `Call`, `Write`）。
3. **结果**：若 `Stmt` 判定传播成立，则将其定义的 `Symbol/State` 标记为污染并入队。



#### Rule L2-4: 物理回流 (Physical Re-sync)

* **逻辑**：若污染从 `Symbol` 重新流向新的 `State`。
* **信用分操作**：`current_score = MAX_SCORE` (100分，证据重新锚定)。

---

## Phase 3: 信用分收敛与标记 (Convergence)

1. **衰减监控**：每一级 `Symbol-only` 传播都会导致路径信用分下降。
2. **阈值处理**：
* `Score > 0`: 正常传播。
* `Score <= 0`: 传播继续，但该步记录必须标记为 `HEURISTIC_ONLY`。

3. **意义**：这防止了语义泛化导致的“万物皆污染”，同时在报告中量化了可信度。

---

## Phase 4: 结果判定与路径回溯 (Reporting)

### 4.1 最终判定

* **判定条件**：检查 `Taint_Symbol_Pool[Sink_Symbol]`。
* **输出**：若存在映射，则报告漏洞，并根据最终 `Score` 给出置信度（High/Medium/Low）。

### 4.2 证据路径重构算法

利用 `Evidence_Journal` 存储的 `StepRecord` (包含 `from_node`, `to_node`, `stmt_id`, `rule_type`)：

1. **逆向搜寻**：从 `Sink` 节点开始，通过 `predecessor` 指针向上追溯。
2. **链条对齐**：将 `State` 的物理跳转、`Symbol` 的语义平移、以及 `Stmt` 的放大规则按时序组合。
3. **三位一体输出**：
* **Tainted Symbols**: 路径中所有参与的语义实体。
* **Tainted States**: 路径中所有被捕获的物理值。
* **Stmt Trace**: 构成攻击路径的源代码行序列。

---

## 5. 实现者避坑指南 (Engineering Notes)

* **关于 Stmt 的副作用**：在 Rule L2-3 中，同一个 Stmt 可能被多个污染源同时激活（例如 `z = x + y`，`x` 和 `y` 都脏），引擎应支持 SourceID 的并集操作。
* **关于上下文**：`ContextID` 必须参与 `Visited` 集合的 Key 构造，否则在处理递归或多重调用时，`Symbol_Taint` 会发生灾难性的路径混淆。
* **关于内存**：`Evidence_Journal` 可能会很大，建议在非 Debug 模式下仅存储每个节点的“最优前驱（Highest Score Predecessor）”。
