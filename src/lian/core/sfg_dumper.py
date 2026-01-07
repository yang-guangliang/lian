from lian.config import config
from lian.config.constants import ANALYSIS_PHASE_ID, SFG_NODE_KIND, SFG_EDGE_KIND
from lian.common_structs import SFGNode, Symbol, State
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from lian.util import util
from lian.util.loader import Loader


# Class-level constants for styling
NODE_STYLES = {
    SFG_NODE_KIND.STMT: {
        "shape": "box",
        # "style": "filled",
        # "fillcolor": "#E8F0FE",
        # "color": "#2B65D9",
        "margin": "0.1",
    },
    SFG_NODE_KIND.SYMBOL: {
        "shape": "box",
        "style": "filled",
        "fillcolor": "#E9F7EF",
        "color": "#1E8449",
        "margin": "0.1",
    },
    SFG_NODE_KIND.STATE: {
        "shape": "box",
        "style": "filled,dashed",
        "fillcolor": "#FFF4E6",
        "color": "#D35400",
        "margin": "0.1",
    }
}

EDGE_COLOR = {
    SFG_EDGE_KIND.SYMBOL_IS_DEFINED: "#1E8449",
    SFG_EDGE_KIND.SYMBOL_IS_USED: "#2B65D9",
    SFG_EDGE_KIND.STATE_IS_USED: "#8E44AD",
    SFG_EDGE_KIND.SYMBOL_STATE: "#D35400",
    SFG_EDGE_KIND.SYMBOL_FLOW: "#27AE60",
    SFG_EDGE_KIND.INDIRECT_SYMBOL_FLOW: "#2ECC71",
    SFG_EDGE_KIND.INDIRECT_SYMBOL_STATE: "#E67E22",
    SFG_EDGE_KIND.STATE_INCLUSION: "#9B59B6",
    SFG_EDGE_KIND.INDIRECT_STATE_INCLUSION: "#8E44AD",
    SFG_EDGE_KIND.CALL_RETURN: "#3498DB",
    SFG_EDGE_KIND.STATE_COPY: "#F39C12",
    SFG_EDGE_KIND.REGULAR: "#7F8C8D",
}

DEFAULT_NODE_STYLE = {
    "shape": "box",
    "style": "filled",
    "fillcolor": "#F2F2F2",
    "color": "#666666",
    "margin": "0.1",
}

BASE_NODE_ATTRS = {
    "style": "filled",
    "fontsize": "10",
    "fontname": "Helvetica",
    "fontcolor": "#111111"
}

BASE_EDGE_ATTRS = {
    "fontsize": "9",
    "fontname": "Helvetica",
    "penwidth": "1.2",
    "color": "#444444",
    "style": "solid",
}

DOT_ESCAPE_TABLE = str.maketrans({
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n"
})


class SFGDumper:
    """
    Dump a state-flow graph (networkx graph, nodes are SFGNode) to DOT with coloring.
    Each node is an SFGNode with three types: symbol, state, stmt.
    """

    def __init__(self, loader, options, phase_id, entry_point, symbol_state_space, graph, taint_manager=None):
        self.loader: Loader = loader
        self.options = options
        self.phase_id = phase_id
        self.entry_point = entry_point
        self.symbol_state_space = symbol_state_space
        self.graph = graph
        # Optional: used to highlight tainted nodes in DOT.
        # Expect interface: get_symbol_tag(symbol_id) / get_state_tag(state_id)
        self.taint_manager = taint_manager

        # Pre-allocate results list
        self.results: List[str] = []

        # Compute output path
        self.file_name = self._compute_output_path(phase_id, entry_point, options.workspace)

        # Node ID mapping
        self.node_id_map: Dict[Any, str] = {}
        self.node_id_seq = 0

        # Constants
        self.MAX_VALUE_LENGTH = 50

    def _compute_output_path(self, phase_id: int, entry_point: str, workspace: str) -> str:
        """Compute output file path based on phase."""
        if phase_id == ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS:
            dir_name = config.STATE_FLOW_GRAPH_P3_DIR
        else:
            dir_name = config.STATE_FLOW_GRAPH_P2_DIR
        method_name = self.loader.convert_method_id_to_method_name(entry_point)
        return str(Path(workspace) / dir_name / f"{method_name}_{entry_point}.dot")

    # ---------- Basic utilities ----------
    def dot_escape(self, s: Any) -> str:
        """Escape special characters for DOT format."""
        if s is None or s == "":
            return ""
        return str(s).translate(DOT_ESCAPE_TABLE)

    def get_node_uid(self, node) -> str:
        """Generate unique ID for each node (cached)."""
        if node not in self.node_id_map:
            self.node_id_seq += 1
            self.node_id_map[node] = f"n{self.node_id_seq}"
        return self.node_id_map[node]

    # ---------- Symbol/state info extraction ----------
    def _get_space_item(self, index: int) -> Optional[Any]:
        """Safely retrieve item from symbol state space."""
        if 0 <= index < len(self.symbol_state_space):
            return self.symbol_state_space[index]
        return None

    def get_symbol_label(self, node: SFGNode) -> str:
        """Get detailed information for symbol node from symbol state space."""
        info = []

        # Basic info from node
        if node.name:
            info.append(f"name={node.name}")
        if node.def_stmt_id >= 0:
            info.append(f"stmt_id={node.def_stmt_id}")
        if node.node_id >= 0:
            info.append(f"symbol_id={node.node_id}")
        if node.index >= 0:
            info.append(f"index={node.index}")
        if node.context_id >= 0:
            info.append(f"context={node.context_id}")

        # Detailed info from symbol state space
        if self.options.complete_graph:
            symbol = self._get_space_item(node.index)
            if isinstance(symbol, Symbol):
                if len(node.name) == 0 and symbol.name:
                    info.append(f"name={symbol.name}")
                if symbol.source_unit_id >= 0:
                    info.append(f"source_unit_id={symbol.source_unit_id}")
                if symbol.default_data_type:
                    info.append(f"data_type={symbol.default_data_type}")
                if symbol.states:
                    info.append(f"states={symbol.states}")

        return ",".join(info)

    def get_state_label(self, node: SFGNode) -> str:
        """Get detailed information for state node from symbol state space."""
        info = []

        # Basic info from node
        if node.def_stmt_id >= 0:
            info.append(f"stmt_id={node.def_stmt_id}")
        if node.node_id >= 0:
            info.append(f"state_id={node.node_id}")
        if node.index >= 0:
            info.append(f"index={node.index}")
        if node.def_stmt_id >= 0:
            info.append(f"stmt_id={node.def_stmt_id}")
        if node.context_id >= 0:
            info.append(f"context={node.context_id}")
        if node.access_path:
            info.append(f"access_path={util.access_path_formatter(node.access_path)}")

        # Detailed info from symbol state space
        if self.options.complete_graph:
            state = self._get_space_item(node.index)
            if isinstance(state, State):
                if state.data_type:
                    info.append(f"data_type={state.data_type}")
                if state.value is not None:
                    value_str = str(state.value)
                    if len(value_str) > self.MAX_VALUE_LENGTH:
                        info.append(f"value={value_str[:self.MAX_VALUE_LENGTH]}...")
                    else:
                        info.append(f"value={value_str}")
                if state.state_type != 0:
                    info.append(f"state_type={state.state_type}")
                if state.source_symbol_id >= 0:
                    info.append(f"source_symbol_id={state.source_symbol_id}")
                if state.source_state_id >= 0 and state.source_state_id != state.state_id:
                    info.append(f"source_state_id={state.source_state_id}")
                if state.tangping_flag:
                    info.append("tangping=true")
        return ",".join(info)

    def get_stmt_label(self, node: SFGNode) -> str:
        """Get statement-specific fields."""
        info = []
        if node.def_stmt_id >= 0:
            info.append(f"stmt_id={node.def_stmt_id}")
        if node.name:
            info.append(f"name={node.name}")
        if node.line_no >= 0:
            info.append(f"line={int(node.line_no)}")
        if node.context_id > 0:
            info.append(f"context={node.context_id}")
        if node.operation:
            info.append(f"operation={node.operation}")

        if self.options.complete_graph:
            unit_id = self.loader.convert_stmt_id_to_unit_id(node.def_stmt_id)
            if unit_id >= 0:
                info.append(f"unit_id={unit_id}")
                unit_info = self.loader.convert_module_id_to_module_info(unit_id)
                if unit_info:
                    info.append(f"unit={unit_info.original_path}")

        return ",".join(info)

    def format_attrs(self, attrs: Dict[str, Any]) -> str:
        """
        Format attribute dictionary into a DOT-compatible string.
        Ensures proper quoting and handles special cases like 'label'.
        """
        formatted_attrs = []
        for key, value in attrs.items():
                formatted_attrs.append(f'{key}="{value}"')
        return " ".join(formatted_attrs)

    def get_node_info(self, node: SFGNode) -> str:
        """Build attribute string for node."""
        attrs = NODE_STYLES.get(node.node_type, DEFAULT_NODE_STYLE).copy()
        attrs.update(BASE_NODE_ATTRS)

        node_type = node.node_type
        if node_type == SFG_NODE_KIND.STMT:
            label = f"Stmt({self.get_stmt_label(node)})"
        elif node_type == SFG_NODE_KIND.SYMBOL:
            label = f"Symbol({self.get_symbol_label(node)})"
        elif node_type == SFG_NODE_KIND.STATE:
            label = f"State({self.get_state_label(node)})"
        else:
            label = "UNKNOWN"

        # Highlight tainted SYMBOL/STATE nodes with special color.
        if self.taint_manager is not None:
            try:
                if node_type == SFG_NODE_KIND.SYMBOL:
                    tag = self.taint_manager.get_symbol_tag(node.node_id)
                    if tag:
                        attrs["fillcolor"] = "#FDEDEC"
                        attrs["color"] = "#C0392B"
                        attrs["penwidth"] = "2.2"
                        attrs["style"] = "filled,bold"
                elif node_type == SFG_NODE_KIND.STATE:
                    tag = self.taint_manager.get_state_tag(node.node_id)
                    if tag:
                        attrs["fillcolor"] = "#FDEDEC"
                        attrs["color"] = "#C0392B"
                        attrs["penwidth"] = "2.2"
                        # keep dashed state style, but make it bold
                        attrs["style"] = "filled,dashed,bold"
            except Exception:
                # Best-effort highlighting; never break dumping.
                pass

        attrs["label"] = self.dot_escape(label)

        return self.format_attrs(attrs)

    def get_edge_label(self, edge) -> str:
        parts = []
        parts.append(f"{SFG_EDGE_KIND.reverse(edge.edge_type).lower()}")

        if edge.pos >= 0:
            parts.append(f"pos={edge.pos}")
        if edge.round >= 0:
            parts.append(f"round={edge.round}")
        if edge.name:
            parts.append(f"name={edge.name}")

        if edge.stmt_id >= 0:
            return f"{edge.stmt_id}:" + ",".join(parts)
        return ",".join(parts)

    def get_edge_info(self, edge) -> str:
        """Return attribute string for DOT edge based on edge type."""
        attrs = BASE_EDGE_ATTRS.copy()
        if edge.edge_type in EDGE_COLOR:
            attrs["color"] = EDGE_COLOR[edge.edge_type]
        attrs["label"] = self.dot_escape(self.get_edge_label(edge))
        return self.format_attrs(attrs)

    def emit_header(self) -> None:
        """Emit DOT graph header."""
        self.results.extend([
            "digraph sfg {",
            '  graph [fontsize=12, labelloc="t"];',
            '  node  [fontsize=10, fontname="Helvetica"];',
            '  edge  [fontsize=9,  fontname="Helvetica"];'
        ])

    def emit_footer(self) -> None:
        """Emit DOT graph footer."""
        self.results.append("}")

    def emit_nodes(self) -> None:
        """Emit all nodes to DOT format."""
        for node in self.graph.nodes():
            uid = self.get_node_uid(node)
            attrs = self.get_node_info(node)
            self.results.append(f"  {uid} [{attrs}];")

    def emit_edges(self) -> None:
        """Emit all edges to DOT format."""
        for u, v, data in self.graph.edges(data=True):
            u_id = self.get_node_uid(u)
            v_id = self.get_node_uid(v)
            attrs = ""
            if "weight" in data:
                attrs = self.get_edge_info(data["weight"])
            self.results.append(f"  {u_id} -> {v_id} [{attrs}];")

    def dump_to_file(self) -> str:
        """Dump the complete SFG to DOT file."""
        self.emit_header()
        self.emit_nodes()
        self.emit_edges()
        self.emit_footer()

        # Write with explicit encoding
        with open(self.file_name, "w", encoding="utf-8") as f:
            f.write("\n".join(self.results))

        return self.file_name
