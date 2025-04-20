# def f():
#     l = [1,2,3,4]
#     b = 1
#     c = 2
#     d = 0
#     for i in l:
#         d = b + c
#         f = d + 3

# import networkx as nx

# def find_paths(G, start_node):
#     all_paths = []

#     def dfs(current_node, current_path):
#         current_path.append(current_node)

#         for succ in G.successors(current_node):
#             edge_weight = G.get_edge_data(current_node, succ)['weight']
#             for w in edge_weight:
#                 dfs(succ, current_path + [w])

#         if not list(G.successors(current_node)):
#             all_paths.append((current_path.copy()))

#         elif len(current_path) > 1:
#             all_paths.append(current_path.copy())

#         current_path.pop()

#     dfs(start_node, [])

#     return all_paths

# # 示例用法
# G = nx.DiGraph()
# G.add_edge(1, 2, weight=[21, 22, 23])
# G.add_edge(1, 3, weight=[31])
# G.add_edge(2, 4, weight=[41, 42])
# G.add_edge(1, 4, weight=[51])

# start_node = 1
# paths = find_paths(G, start_node)

# # 输出结果
# for path in paths:
#     print(path)

import networkx as nx

def find_paths(G, start_node):
    # 初始化结果列表
    all_paths = []

    # 递归函数，用来查找所有的路径
    def dfs(current_node, current_path, visited):
        # 将当前节点加入路径和已访问集合
        current_path.append(current_node)
        visited.add(current_node)

        # 对于每个后继节点，递归查找路径
        for succ in G.successors(current_node):
            if succ not in visited:  # 避免环和自循环
                edge_weight = G.get_edge_data(current_node, succ)['weight']
                for w in edge_weight:
                    dfs(succ, current_path + [w], visited)

        # 如果当前节点是一个叶子节点（没有后继节点），保存路径
        if not list(G.successors(current_node)):
            all_paths.append(tuple(current_path.copy()))

        # 如果已经遍历到非叶子节点，路径同样要保存
        elif len(current_path) > 1:
            all_paths.append(tuple(current_path.copy()))

        # 递归结束后，回溯
        current_path.pop()
        visited.remove(current_node)

    # 从起始节点开始DFS，初始化 visited 集合
    dfs(start_node, [], set())

    return all_paths


G = nx.DiGraph()
G.add_edge(1, 2, weight=[21, 51])
G.add_edge(2, 3, weight=[31])
G.add_edge(3, 1, weight=[11])  # 形成一个环
G.add_edge(2, 4, weight=[41])
print(find_paths(G, 1))

