## Language Frontend

The language parsing frontend converts source code into a unified intermediate representation (IR), enabling language-agnostic semantic analysis through subsequent IR-based processing. However, existing IRs like LLVM IR and Graal Truffle suffer from complexity, and many tools require frontends to handle additional tasks such as type analysis, control flow analysis, and SSA conversion. This significantly increases frontend development complexity and raises the cost of source code transformation.

To address this challenge, we implemented a **lightweight language frontend** that offloads all semantics-related logic to the semantic analysis engine. The frontend focuses solely on faithfully translating source code into our intermediate language, **GIR (General IR)**. Designed to be type-system-agnostic, GIR strips away redundant type-related details and emphasizes **code behavior modeling** and **variable logic relationships**, enabling higher-level program behavior analysis.

Currently, GIR contains only **78 core instructions**. For details, refer to the [GIR Documentation](gir.md). These instructions follow intuitive semantic naming conventions, such as:  
- `class_decl` (class declaration)  
- `call_stmt` (function call)  
- `assign_stmt` (assignment statement)  

## Implementation Workflow
1. **AST Generation**: Use **Tree-sitter** to parse source code into an Abstract Syntax Tree (AST).  
2. **GIR Conversion**: The language-specific parser (`lang_parser.py`) transforms the AST into GIR using a **top-down recursive approach**.
