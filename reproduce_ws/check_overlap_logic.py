
import sys
import os
sys.path.append("/home/gxm/lian/src")
from lian.util.data_model import DataModel
from lian.config import config

ws = "/home/gxm/lian/reproduce_ws/lian_workspace"
module_symbols_path = os.path.join(ws, "frontend/module_symbols")

ms = DataModel().load(module_symbols_path)
print(f"Config START_INDEX: {config.START_INDEX}")
print(f"Module Symbol Count (len): {len(ms)}")
max_module_id = -1
min_module_id = 999999

for row in ms:
    if row.module_id > max_module_id:
        max_module_id = row.module_id
    if row.module_id < min_module_id:
        min_module_id = row.module_id

print(f"Min Module ID: {min_module_id}")
print(f"Max Module ID: {max_module_id}")

# Simulate LangAnalysis init_start_stmt_id logic
# From src/lian/lang/lang_analysis.py:350
# result = len(symbol_table)
# adjust_node_id...

def adjust_node_id(node_id):
    node_id += config.MIN_ID_INTERVAL
    remainder = node_id % 10
    if remainder != 0:
        node_id += (10 - remainder)
    return node_id

start_stmt_id = adjust_node_id(len(ms))
print(f"Calculated Start STMT ID (based on Code): {start_stmt_id}")

if start_stmt_id < max_module_id:
    print(f"CONCLUSION: Start ID ({start_stmt_id}) is LESS than Max Module ID ({max_module_id}).")
    print("This PROVES overlap/collision is possible as stmt_id grows.")
else:
    print("CONCLUSION: Start ID is safe?")
