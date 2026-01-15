
import sys
import os
import pprint
sys.path.append("/home/gxm/lian/src")
from lian.util.data_model import DataModel
from lian.config import constants
from lian.config.constants import LIAN_SYMBOL_KIND

ws = "/home/gxm/lian/reproduce_ws/lian_workspace"
module_symbols_path = os.path.join(ws, "frontend/module_symbols")
import_graph_nodes_path = os.path.join(ws, "semantic_p1/import_graph_nodes")

# Load module symbols
ms = DataModel().load(module_symbols_path)
module_map = {}
print("Loading Module Symbols...")
for row in ms:
    module_map[row.module_id] = row

# Load import graph nodes
# Since save_import_graph_nodes saves dict, DataModel().load() should load it.
# Check Loader.save_import_graph_nodes implementation details in loader.py 
# if it uses DataModel or pickle.
# Assuming DataModel for now.
print("Loading Import Graph Nodes...")
ign = DataModel().load(import_graph_nodes_path)
graph_nodes = {}
for row in ign:
    # row is likely just the value object if normalized, or key-value pair.
    # checking structure.
    # Loader usually flattens/unflattens.
    # If saved as DataModel, let's see what columns are.
    pass

# Direct inspection of DataModel
print(f"Number of graph nodes: {len(ign)}")

collision_count = 0
fake_node_count = 0

for row in ign:
    # row attributes depend on SymbolNodeInImportGraph structure and flatten logic.
    # Assuming attributes: symbol_id, symbol_type, symbol_name...
    
    # Check for negative IDs
    if row.symbol_id < 0:
        fake_node_count += 1
        # print(f"Fake Node found: {row.symbol_id} {row.symbol_name}")

    if row.symbol_id in module_map:
        module_info = module_map[row.symbol_id]
        # Check if types match
        # Module types: MODULE_SYMBOL (0), UNIT_SYMBOL (1)
        if row.symbol_type not in [LIAN_SYMBOL_KIND.MODULE_SYMBOL, LIAN_SYMBOL_KIND.UNIT_SYMBOL]:
            print(f"COLLISION DETECTED at ID {row.symbol_id}!")
            print(f"  Original Module: {module_info.symbol_name} (Type: {module_info.symbol_type})")
            print(f"  Current Node:    {row.symbol_name} (Type: {row.symbol_type})")
            collision_count += 1

print(f"Total Collisions: {collision_count}")
print(f"Total Fake Nodes: {fake_node_count}")
