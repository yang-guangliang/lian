def graph_successors(graph, node):
    if node in graph:
        return graph.successors(node)
    return []
def access_path_formatter(state_access_path):
    key_list = []
    for item in state_access_path:
        key = item.key
        key = key if isinstance(key, str) else str(key)
        if key != "":
            key_list.append(key)

    # 使用点号连接所有 key 值
    access_path = '.'.join(key_list)
    return access_path