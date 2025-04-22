## 1. Scope Hierarchy Analysis

Scope analysis is used to determine the effective range of symbols (including variables, functions, classes, etc.), identifying where in the code a symbol is valid. The analysis probes the entire file's scope structure, clarifies the symbols contained within each scope, and stores scope and symbol information in a tree-like structure.

## 2. Entry Points Search

Entry points are determined by the `find_entry_point()` function in `basic_analysis.py`. Custom entry functions can be defined in the `entry_point_rule` field of the `EntryPointGenerator` class in the `entry_point.py` file based on actual requirements.

## 3. Control Flow Analysis

Control flow analysis is used to construct control flow graphs (CFGs) for program methods. Its core logic involves traversing statements in the function body and invoking corresponding handler functions based on statement types to build directed graphs representing program execution paths.  

The analyzer first processes the function parameter initialization block, then analyzes the function body while connecting statement nodes. For control structures like if/while/for, it recursively analyzes their inner blocks and handles true/false branches or loop back edges. Special statements such as break/continue are collected and processed uniformly outside the loop body, while return statements are directly linked to the exit node.  

Finally, the analyzer merges duplicate edges and resolves goto-label jumps. This implementation supports various programming constructs, including conditional branches, loops, exception handling, and declaration statements. By maintaining predecessor statement lists and special statement lists, it ensures correct control flow connections, ultimately generating complete CFGs for subsequent analysis.

## 4. Instruction-Level Def/Use Analysis

Definition/use analysis (def/use analysis) tracks the definition and reference relationships of symbols (i.e., identifiers) in each statement of a program. At this stage, def/use analysis is flow-insensitive and performed on individual statements. The analysis proceeds statement by statement following the control flow graph (CFG). After analyzing each statement, it generates semantic information (status) for that statement and stores def/use information in two tables: `symbol_to_defined` and `symbol_to_used`. The functions of these two tables are as follows:

1. **`symbol_to_defined` Mapping Table**  
   - Structure: `(method_id, symbol_id, set[stmt_id])`  
   - Function: Within a given method scope, quickly locate all statements that define a specific symbol.

2. **`symbol_to_used` Mapping Table**  
   - Structure: `(method_id, symbol_id, set[stmt_id])`  
   - Function: Within a given method scope, quickly retrieve all statements that use a specific symbol.

## 5. File Dependency (Import Dependency)

For import dependency analysis, a file can use symbols defined in other files. The syntax of import statements is highly flexible—the import target could be a file, a directory, or a symbol. For example:

```python
from A import B  
from A import *  
```

- If `A` is a file, `B` and `*` represent imported symbols.  
- If `A` is a directory, `B` and `*` may represent multiple files or subdirectories.  

Thus, by determining the type and content of `A`, we can resolve the meaning of `B` and `*`.  

Since the scope hierarchy analysis has already determined the scope of each symbol, we first construct an **export symbol table** for each file, storing symbols defined in that file that can be exported.  

Then, based on the specific import statement:  
- If the import target is a **file**, the exported symbols from the target file are added to the importing file's export symbol table (i.e., symbols are "passed" to the importing file).  
- If the import target is a **directory**, the directory itself is added as a symbol to the importing file's export symbol table.  
- If the import target is a **symbol**, that symbol is taken from the target file's export symbol table and added to the importing file's export symbol table.  

## 6. Type Hierarchy

In this step, we analyze the program's type hierarchy, focusing on inheritance relationships between classes. The analysis consists of two phases:  

**Phase 1 (Class-Level Analysis):**  
Using the `analyze_type_hierarchy` function in the scope hierarchy, we extract method information for each class (parent classes are not processed at this stage). Meanwhile, the **type graph** (`type_graph`) stores inheritance relationships between classes and their parents—represented as directed edges with attributes: each edge points from a child class to its parent, with attributes including the parent class name and its inheritance order.  

**Phase 2 (Inheritance Relationship Analysis):**  
We traverse the type graph (`type_graph`). When a class `A` is found to have a parent class `B`, we use topological sorting to iteratively process all successor nodes, merging the method set of parent class `B` into the method set of child class `A`.  

## 7. Function Classification Based on Callees

The final step in basic analysis is **function classification**. In subsequent analyses, functions will be treated as the basic unit of analysis. If a function contains calls to other functions, the callee functions must be analyzed first, and their results applied to the caller function.  

Functions are classified into four categories:  
1. **`no_callees`**: Functions that do not call any other functions.  
2. **`only_direct_callees`**: Functions that only call statically resolvable functions.  
3. **`mixed_direct_callees`**: Functions that call a mix of static and dynamic functions.  
4. **`only_dynamic_callees`**: Functions that only call dynamically resolved functions (e.g., via reflection or runtime binding).  

This classification ensures that the second-phase analysis processes functions in the correct order.  
