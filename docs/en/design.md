# **Architecture**

The LIAN system comprises three core modules, as shown in the diagram below:

![Architecture](../img/structure_en.png)

- [Language Frontend](./lang_parser.md): Converts source code into GIR for standardized processing.

- Semantic Analysis Engine: Implements a layered analysis strategy, including:

  - [Basic analysis](./basic_analysis.md)

  - [Function summary-based analysis](summary_generation.md)

  - [Global analysis](global_analysis.md)
    Generates multi-level semantic results (control flow, data flow, state flow).

- Infrastructure: Provides [memory/file management](loader.md) (previons memory exhaustion) and a [plugin system](plugin.md) for extensibility.
