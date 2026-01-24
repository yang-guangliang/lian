# Lian Program Analysis Framework

## 1 Background

Program analysis is a fundamental technique for understanding program behavior, validating software correctness, and supporting system security. Over the past decades, research on traditional industrial languages such as C/C++ and Java has resulted in relatively mature program analysis methodologies and toolchains. In the C/C++ domain, tools such as SVF and Phasar support precise pointer analysis through detailed modeling of alias relations and heap objects. In the Java domain, frameworks such as Soot and WALA exploit relatively stable type systems and reference semantics to construct reusable points-to analysis infrastructures. These techniques have been widely applied in tasks such as code auditing and vulnerability analysis.

In recent years, however, the programming language ecosystem has shifted. Python has become a primary language in artificial intelligence and data analysis. JavaScript and TypeScript are widely used in frontend and full-stack development, with TypeScript ranking first in the GitHub language popularity index in 2025. Go plays an important role in cloud services and systems programming. Compared with traditional languages such as C/C++ and Java, existing program analysis techniques for these languages often suffer from limitations in precision and scalability.

This gap in analysis capability introduces practical risks to software security and reliability. Complex runtime behaviors are difficult to analyze with strong guarantees, and potential vulnerabilities are often missed during development. As these languages are increasingly deployed in critical domains such as financial systems, cloud infrastructure, and AI platforms, insufficient program analysis support becomes a limiting factor for systematic security analysis of modern software systems.

## 2 Challenges

In these emerging language scenarios, the main difficulties arise from uncertainty in memory models and runtime behavior:

* Type information is often unavailable or unstable at compile time
* Object properties can be dynamically added, removed, or modified
* Dynamic object shapes make field sets difficult to determine statically
* Computed property names and dynamic code loading complicate static resolution of property access and control flow
* Higher-order functions, closures, and dynamic dispatch significantly enlarge potential call target sets
* Dynamic property resolution mechanisms (e.g., prototype chain lookup in JavaScript, or class-hierarchy-based and implicit attribute resolution in Python) cause field resolution to depend on runtime state, obscuring object boundaries and field semantics

These characteristics undermine key assumptions used by traditional program analysis, including stable object layouts, statically known field sets, and type-based constraints for pruning and convergence. As a result, context-sensitive and flow-sensitive pointer analysis becomes substantially more complex, and maintaining effectiveness and scalability for large programs is difficult.

Existing type analysis techniques for dynamic languages, such as TAJS, SAFE, and JSAI, typically rely on abstract interpretation and have achieved progress for specific languages like JavaScript. However, they face structural limitations. Precision must be traded off against heap abstraction and object merging strategies, while branch handling often leads to state splitting and state explosion. Even with widening and similar mechanisms, large-scale analyses still face fundamental precision–efficiency trade-offs.

Another practical issue is that many existing program analysis frameworks are tightly coupled to individual languages. Supporting a new language often requires reimplementing major components from frontend to core analysis, including AST-to-IR translation, control-flow analysis, data-flow analysis, and pointer analysis. This results in high engineering cost and poor reuse across languages.

## 3 Design Rationale

Addressing these challenges requires rethinking program analysis methodology for modern language ecosystems:

* A framework is needed that provides extensible and reusable analysis capabilities with low marginal cost when supporting new languages
* Even under highly dynamic behavior, the framework should support controlled heap abstraction and points-to modeling, reducing reliance on explicit type information

The core objective is to construct a unified, high-precision program analysis framework that can accommodate language diversity.

**Commonality across languages provides the basis for unification.**

Programming languages share fundamental semantic structures:

* Most practical languages are Turing-complete
* Since the 1950s, languages have evolved along imperative, functional, and object-oriented lines, with new languages inheriting and adapting prior designs
* Empirically, languages in the TIOBE Top 50, as well as newer languages such as V and Odin, exhibit substantial syntactic and semantic similarity, including variable manipulation, control flow, function invocation, and object-oriented constructs

Based on this commonality, unification can be achieved at two levels:

* **Syntax level**: language-specific ASTs are translated into a common intermediate representation
* **Semantic level**: all analyses are performed on the unified IR, including scope analysis, type-related analysis, module imports, control flow, data flow, pointer analysis, and taint analysis

Once a language frontend can translate ASTs into the unified IR, analysis capabilities can be provided with limited additional language-specific semantic extensions.

**At the same time, language differences remain essential and must be explicitly handled.**

Key sources of variation include:

* Type systems: many dynamic languages lack static types, while some static languages permit highly permissive types
* Variable declaration rules: some languages omit explicit declarations
* Inheritance models: prototype-based inheritance versus class-based inheritance
* Function calling conventions: explicit `self` parameters versus implicit `this` semantics
* Property access semantics: indexed access may represent arrays, dictionaries, or object properties
* `for..in` constructs: semantics differ significantly across languages

To accommodate these differences, Lian adopts a plugin-based extension mechanism, allowing language-specific behaviors to be integrated without modifying the core analysis logic. Unified analysis provides the structural foundation, while extensibility ensures compatibility.

**Unified analysis does not imply weaker analysis.**

Dynamic features such as missing types, higher-order functions, and dynamic property resolution limit the effectiveness of type-driven analyses. In these settings, precise, type-independent pointer analysis becomes central:

* Object types can be inferred from referenced memory contents
* For calls such as `method()` or `receiver.method()`, pointer analysis can determine the actual callable targets

To remain effective, pointer analysis must address several issues:

* **Field sensitivity**, requiring explicit modeling of field values
* **Memory object abstraction**, extending beyond traditional heap objects
* **Flow sensitivity**, particularly for field-level operations beyond SSA approximations
* **Termination guarantees**, as points-to sets grow large without type constraints

## 4 Architecture

The Lian framework consists of four main components:

* **General Intermediate Representation (GIR)**: a unified IR designed around language commonality; ASTs are translated into GIR, with approximately 1,600 lines of frontend code per language

* **Unified Pointer Analysis Engine**: memory objects are abstracted by address, value, and shape; on-the-fly analysis combined with def–use information supports flow sensitivity

* **Language-Specific Extensions**: a plugin mechanism supports language-specific semantics

* **State-Flow-Graph-Based Taint Analysis**: taint analysis is built on pointer and data-flow results using state flow graphs

## 5 Applications

Lian supports:

* Static detection of software defects
* Security modeling and vulnerability analysis
* Integration with AI-based workflows for model training and inference


## 6 Other Important Notes

### 6-1 Language Support

Current implementation status of Lian language frontends:

| Language   | Status            |
| ---------- | ----------------- |
| Python     | ✅ Fully supported |
| JavaScript | ✅ Fully supported |
| TypeScript | ✅ Fully supported |
| Java       | ✅ Fully supported |
| Go         | ✅ Fully supported |
| C          | ✅ Fully supported |
| PHP        | ✅ Fully supported |
| ArkTS      | ✅ Fully supported |
| LLVM IR    | ✅ Fully supported |
| Rust MIR   | Not mature        |
| C#         | Not mature        |
| Ruby       | Not mature        |
| Smali      | Not mature        |

### 6-2 Core Module Description

```
src/lian/
├── lang/                       # Language frontends
│   ├── xxx_parser.py               # Parser for a specific language
│   ├── common_parser.py            # Common base class for all language parsers
│   └── lang_analysis.py            # Main language analysis entry
├── basics/                     # Basic structural analyses
│   ├── control_flow.py             # Control-flow analysis
│   ├── entry_points.py             # Entry-point identification
│   ├── import_hierarchy.py         # Module import hierarchy analysis
│   ├── scope_hierarchy.py          # Scope hierarchy analysis
│   ├── stmt_def_use_analysis.py    # Definition–use analysis
│   └── type_hierarchy.py           # Type hierarchy analysis
├── core/                       # Core semantic analysis engine
│   ├── global_semantics.py         # Top-down semantic analysis
│   ├── prelim_semantics.py         # Bottom-up semantic analysis
│   ├── resolver.py                 # Resolver
│   └── stmt_states.py              # Statement state analysis
├── taint/                      # Taint analysis
│   ├── taint_analysis.py           # Taint analysis engine
│   ├── taint_structs.py            # Taint analysis data structures
│   └── rule_manager.py             # Rule manager
├── events/                     # Plugin system ensuring extensibility and handling language diversity
│   ├── event_manager.py            # Event manager
│   └── default_event_handlers/     # Default event handlers
├── externs/                    # External system modeling
│   └── extern_system.py            # External system integration
└── util/                       # Utility modules
    ├── loader.py                   # File system management
    ├── data_model.py               # Data model
    └── readable_gir.py             # Human-readable GIR output
```

### 6-3 Configuration Options

Through configuration files under the `default_settings/` directory, users can customize:

* `entry.yaml`: entry point rule configuration
* `source.yaml`: taint source rule configuration
* `sink.yaml`: taint sink rule configuration
* `propagation.yaml`: taint propagation rule configuration

## 7 Summary

Lian is independently developed by the System Software and Reliability Group at Fudan University. It is based on a general intermediate representation and provides unified, high-precision pointer analysis. The framework emphasizes extensibility and language independence, and is intended to support program analysis and security analysis across diverse programming languages with well-defined semantics.