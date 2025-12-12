class SFGDotDumper:
    """
    Dump a state-flow graph (networkx graph, nodes are SFGNode) to DOT with coloring.
    No nested functions are used.
    """

    def __init__(self, loader=None, options=None, phase_id=None, entry_point=None):
        self.loader = loader
        self.options = options
        self.phase_id = phase_id
        self.entry_point = entry_point

        self.node_id_map = {}   # id(node) -> "nX"
        self.node_id_seq = 0

    # ---------- basic utilities ----------
    def dot_escape(self, s):
        if s is None:
            return ""
        s = str(s)
        s = s.replace("\\", "\\\\")
        s = s.replace('"', '\\"')
        s = s.replace("\n", "\\n")
        return s

    def get_node_uid(self, node):
        key = id(node)
        uid = self.node_id_map.get(key)
        if uid is not None:
            return uid
        self.node_id_seq += 1
        uid = f"n{self.node_id_seq}"
        self.node_id_map[key] = uid
        return uid

    def is_multi_graph(self, graph):
        return isinstance(graph, (nx.MultiDiGraph, nx.MultiGraph))

    # ---------- enum name helpers ----------
    def node_kind_name(self, node):
        try:
            return SFG_NODE_KIND[node.node_type]
        except Exception:
            return "UNKNOWN"

    def edge_kind_name(self, edge_data):
        # edge_data may be SFGEdge, dict, or other
        try:
            return SFG_EDGE_KIND[edge_data.edge_type]
        except Exception:
            pass
        try:
            edge_type = edge_data.get("edge_type", None)
            if edge_type is not None:
                return SFG_EDGE_KIND[edge_type]
        except Exception:
            pass
        return "EDGE"

    def extract_edge_obj(self, edge_data):
        """
        Normalize edge payload.
        - If edge_data is SFGEdge => return it
        - If edge_data is dict and contains "obj" => return dict["obj"]
        - else return edge_data itself
        """
        if isinstance(edge_data, dict) and "obj" in edge_data:
            return edge_data["obj"]
        return edge_data

    # ---------- styling ----------
    def node_style(self, node):
        """
        Return attribute dict for DOT node.
        """
        attrs = {
            "style": "filled",
            "fontsize": "10",
            "fontname": "Helvetica",
        }

        try:
            nt = node.node_type
        except Exception:
            nt = None

        if nt == SFG_NODE_KIND.STMT:
            attrs["shape"] = "box"
            attrs["fillcolor"] = "#E8F0FE"
            attrs["color"] = "#2B65D9"
            attrs["fontcolor"] = "#111111"
        elif nt == SFG_NODE_KIND.SYMBOL:
            attrs["shape"] = "ellipse"
            attrs["fillcolor"] = "#E9F7EF"
            attrs["color"] = "#1E8449"
            attrs["fontcolor"] = "#111111"
        elif nt == SFG_NODE_KIND.STATE:
            attrs["shape"] = "diamond"
            attrs["fillcolor"] = "#FFF4E6"
            attrs["color"] = "#D35400"
            attrs["fontcolor"] = "#111111"
        else:
            attrs["shape"] = "box"
            attrs["fillcolor"] = "#F2F2F2"
            attrs["color"] = "#666666"
            attrs["fontcolor"] = "#111111"

        return attrs

    def edge_style(self, edge_obj):
        """
        Return attribute dict for DOT edge.
        """
        attrs = {
            "fontsize": "9",
            "fontname": "Helvetica",
            "penwidth": "1.2",
            "color": "#444444",
            "style": "solid",
            "label": "",
        }

        name = self.edge_kind_name(edge_obj)

        if name == "SYMBOL_IS_DEFINED":
            attrs["color"] = "#1E8449"
            attrs["penwidth"] = "1.8"
            attrs["label"] = "def"
        elif name == "SYMBOL_IS_USED":
            attrs["color"] = "#2B65D9"
            attrs["penwidth"] = "1.6"
            attrs["label"] = "use"
        elif name == "STATE_IS_USED":
            attrs["color"] = "#8E44AD"
            attrs["penwidth"] = "1.4"
            attrs["style"] = "dashed"
            attrs["label"] = "state-use"
        elif name == "SYMBOL_STATE":
            attrs["color"] = "#D35400"
            attrs["penwidth"] = "1.4"
            attrs["label"] = "sym->state"
        else:
            attrs["label"] = name.lower()

        # optional pos label
        pos = None
        try:
            pos = edge_obj.pos
        except Exception:
            try:
                pos = edge_obj.get("pos", None)
            except Exception:
                pos = None
        if pos is not None and attrs["label"]:
            attrs["label"] = f'{attrs["label"]}[{pos}]'
        elif pos is not None:
            attrs["label"] = f'[{pos}]'

        return attrs

    # ---------- label building ----------
    def build_node_label(self, node):
        """
        Make a compact multi-line label.
        """
        try:
            kind = self.node_kind_name(node).lower()
        except Exception:
            kind = "node"

        parts = [kind]

        # common fields
        def_stmt_id = getattr(node, "def_stmt_id", -1)
        if isinstance(def_stmt_id, int) and def_stmt_id > 0:
            parts.append(f"stmt_id={def_stmt_id}")

        context_id = getattr(node, "context_id", 0)
        if isinstance(context_id, int) and context_id > 0:
            parts.append(f"ctx={context_id}")

        # typed fields
        node_type = getattr(node, "node_type", None)

        if node_type == SFG_NODE_KIND.STMT:
            name = getattr(node, "name", None)
            if name:
                parts.append(f"op={name}")
            line_no = getattr(node, "line_no", 0)
            if isinstance(line_no, int) and line_no > 0:
                parts.append(f"line={line_no}")

        elif node_type == SFG_NODE_KIND.SYMBOL:
            nm = getattr(node, "name", None)
            if nm:
                parts.append(f"name={nm}")
            node_id = getattr(node, "node_id", None)
            if node_id is not None:
                parts.append(f"id={node_id}")
            idx = getattr(node, "index", -1)
            if isinstance(idx, int) and idx >= 0:
                parts.append(f"idx={idx}")

        elif node_type == SFG_NODE_KIND.STATE:
            node_id = getattr(node, "node_id", None)
            if node_id is not None:
                parts.append(f"state_id={node_id}")
            idx = getattr(node, "index", -1)
            if isinstance(idx, int) and idx >= 0:
                parts.append(f"idx={idx}")
            ap = getattr(node, "access_path", None)
            if ap:
                try:
                    parts.append(util.access_path_formatter(ap))
                except Exception:
                    parts.append(str(ap))

        return "\\n".join(parts)

    # ---------- DOT emission ----------
    def format_attr_dict(self, attrs):
        """
        attrs: dict[str,str]
        return: 'k="v",k2="v2"...'
        """
        if attrs is None:
            return ""
        items = []
        # stable order for diff-friendly output
        for k in sorted(attrs.keys()):
            v = attrs[k]
            items.append(f'{k}="{self.dot_escape(v)}"')
        return ",".join(items)

    def emit_header(self, lines):
        lines.append("digraph sfg {")
        lines.append('  graph [rankdir=LR, fontsize=12, labelloc="t"];')
        lines.append('  node  [fontsize=10, fontname="Helvetica"];')
        lines.append('  edge  [fontsize=9,  fontname="Helvetica"];')
        if self.entry_point is not None:
            lines.append(f'  label="{self.dot_escape(self.entry_point)}";')

    def emit_footer(self, lines):
        lines.append("}")

    def emit_nodes(self, graph, lines):
        for node in list(graph.nodes()):
            uid = self.get_node_uid(node)
            label = self.build_node_label(node)
            attrs = self.node_style(node)
            attrs["label"] = label
            lines.append(f"  {uid} [{self.format_attr_dict(attrs)}];")

    def emit_edges(self, graph, lines):
        if self.is_multi_graph(graph):
            for u, v, k, data in graph.edges(keys=True, data=True):
                u_id = self.get_node_uid(u)
                v_id = self.get_node_uid(v)
                edge_obj = self.extract_edge_obj(data)
                eattrs = self.edge_style(edge_obj)
                lines.append(f"  {u_id} -> {v_id} [{self.format_attr_dict(eattrs)}];")
        else:
            for u, v, data in graph.edges(data=True):
                u_id = self.get_node_uid(u)
                v_id = self.get_node_uid(v)
                edge_obj = self.extract_edge_obj(data)
                eattrs = self.edge_style(edge_obj)
                lines.append(f"  {u_id} -> {v_id} [{self.format_attr_dict(eattrs)}];")

    def dump_to_file(self, graph, file_name):
        if graph is None or len(graph) == 0:
            return
        lines = []
        self.emit_header(lines)
        self.emit_nodes(graph, lines)
        self.emit_edges(graph, lines)
        self.emit_footer(lines)

        with open(file_name, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))