#!/usr/bin/env python3

import init_test
from lian.common_structs import PathManager, CallPath, CallSite, PathTrie

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_paths(manager, title="当前路径"):
    print(f"\n{title}:")
    for p in manager.paths:
        path_str = " -> ".join([f"({cs.caller_id},{cs.call_stmt_id},{cs.callee_id})" for cs in p.path])
        print(f"  [{len(p)}] {path_str}")

# ============================================================================
# 测试 1: 基础规则 - 不同分支可共存
# ============================================================================
print_section("测试 1: 不同分支可共存")

manager = PathManager()

path1 = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5),
    CallSite(5, 6, 7),
    CallSite(7, 8, 9),
    CallSite(9, 10, 11)
))

path2 = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5),
    CallSite(5, 12, 13)  # 不同分支
))

path3 = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 14, 15)  # 不同分支
))

print("\n1.1 添加三条有公共前缀但分支不同的路径")
assert manager.add_path(path1) == True
print(f"✓ 添加 path1")

assert manager.add_path(path2) == True
print(f"✓ 添加 path2 (与path1在第3个节点分叉)")

assert manager.add_path(path3) == True
print(f"✓ 添加 path3 (与path1在第2个节点分叉)")

print_paths(manager)
assert len(manager.paths) == 3, "Should have 3 paths"
assert path1 in manager.paths
assert path2 in manager.paths
assert path3 in manager.paths
print(f"\n✓ 三条路径都保留（不同分支）")

print("\n1.2 尝试添加它们的公共前缀 - 应该被拒绝")
prefix1 = CallPath((CallSite(1, 2, 3),))
assert manager.add_path(prefix1) == False
print(f"✓ 拒绝前缀 (1,2,3) - 因为存在更长的路径")

prefix2 = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5)
))
assert manager.add_path(prefix2) == False
print(f"✓ 拒绝前缀 (1,2,3)->(3,4,5) - 因为存在更长的路径")

print_paths(manager)
assert len(manager.paths) == 3
print(f"\n✓ 所有路径仍然保留")

# ============================================================================
# 测试 2: 同一分支上的前缀关系
# ============================================================================
print_section("测试 2: 同一分支上的前缀关系")

manager2 = PathManager()

short_path = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5)
))

long_path = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5),
    CallSite(5, 6, 7)
))

print("\n2.1 先添加短路径，再添加长路径")
assert manager2.add_path(short_path) == True
print(f"✓ 添加短路径")
print_paths(manager2)

assert manager2.add_path(long_path) == True
print(f"✓ 添加长路径 - 短路径被删除")
print_paths(manager2)

assert short_path not in manager2.paths, "Short path should be removed"
assert long_path in manager2.paths, "Long path should exist"
assert len(manager2.paths) == 1
print(f"\n✓ 长路径替换了短路径")

print("\n2.2 删除长路径，重新测试")
manager2.remove_path(long_path)

print("\n2.3 先添加长路径，再尝试添加短路径")
assert manager2.add_path(long_path) == True
print(f"✓ 添加长路径")
print_paths(manager2)

assert manager2.add_path(short_path) == False
print(f"✓ 拒绝短路径 - 因为长路径已存在")
print_paths(manager2)

assert long_path in manager2.paths
assert short_path not in manager2.paths
assert len(manager2.paths) == 1
print(f"\n✓ 只保留长路径")

# ============================================================================
# 测试 3: 复杂的多层分支结构
# ============================================================================
print_section("测试 3: 复杂的多层分支结构")

manager3 = PathManager()

"""
构建如下树结构:
        (1,2,3)
       /        \
   (3,4,5)    (3,14,15)
   /     \
(5,6,7) (5,12,13)
   |
(7,8,9)
"""

branch_a = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5),
    CallSite(5, 6, 7),
    CallSite(7, 8, 9)
))

branch_b = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5),
    CallSite(5, 12, 13)
))

branch_c = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 14, 15)
))

print("\n3.1 添加三个分支")
assert manager3.add_path(branch_a) == True
assert manager3.add_path(branch_b) == True
assert manager3.add_path(branch_c) == True

print_paths(manager3, "三个分支")
assert len(manager3.paths) == 3
print(f"\n✓ 三个不同分支都保留")

print("\n3.2 尝试添加各级公共前缀 - 都应该被拒绝")
assert manager3.add_path(CallPath((CallSite(1, 2, 3),))) == False
print(f"✓ 拒绝 level-1 前缀")

assert manager3.add_path(CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5)
))) == False
print(f"✓ 拒绝 level-2 前缀")

assert manager3.add_path(CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5),
    CallSite(5, 6, 7)
))) == False
print(f"✓ 拒绝 level-3 前缀 (branch_a 的前缀)")

print_paths(manager3, "所有前缀被拒绝后")
assert len(manager3.paths) == 3
print(f"\n✓ 三个分支仍然保留")

print("\n3.3 添加 branch_a 的扩展")
branch_a_extended = CallPath((
    CallSite(1, 2, 3),
    CallSite(3, 4, 5),
    CallSite(5, 6, 7),
    CallSite(7, 8, 9),
    CallSite(9, 10, 11)  # 扩展
))

assert manager3.add_path(branch_a_extended) == True
print(f"✓ 添加 branch_a 的扩展路径")

print_paths(manager3, "添加扩展后")
assert branch_a not in manager3.paths, "Original branch_a should be removed"
assert branch_a_extended in manager3.paths
assert branch_b in manager3.paths, "branch_b should still exist"
assert branch_c in manager3.paths, "branch_c should still exist"
assert len(manager3.paths) == 3
print(f"\n✓ branch_a 被扩展版本替换，其他分支保留")

# ============================================================================
# 测试 4: 边界情况
# ============================================================================
print_section("测试 4: 边界情况")

manager4 = PathManager()

print("\n4.1 单节点路径")
single = CallPath((CallSite(100, 101, 102),))
assert manager4.add_path(single) == True
print_paths(manager4)
print(f"✓ 单节点路径添加成功")

print("\n4.2 扩展单节点路径")
single_ext = CallPath((
    CallSite(100, 101, 102),
    CallSite(102, 103, 104)
))
assert manager4.add_path(single_ext) == True
print_paths(manager4)
assert single not in manager4.paths
assert single_ext in manager4.paths
print(f"✓ 扩展路径替换了单节点路径")

print("\n4.3 再次尝试添加单节点 - 应该被拒绝")
assert manager4.add_path(single) == False
print(f"✓ 单节点路径被拒绝")

print("\n4.4 添加负值路径")
negative = CallPath((CallSite(-1, 2, 3),))
assert manager4.add_path(negative) == False
print(f"✓ 负值路径被拒绝")

print("\n4.5 重复添加相同路径")
assert manager4.add_path(single_ext) == False
print(f"✓ 重复路径被拒绝")

# ============================================================================
# 测试 5: 多层嵌套前缀
# ============================================================================
print_section("测试 5: 多层嵌套前缀")

manager5 = PathManager()

level1 = CallPath((CallSite(1, 2, 3),))
level2 = CallPath((CallSite(1, 2, 3), CallSite(3, 4, 5)))
level3 = CallPath((CallSite(1, 2, 3), CallSite(3, 4, 5), CallSite(5, 6, 7)))
level4 = CallPath((CallSite(1, 2, 3), CallSite(3, 4, 5), CallSite(5, 6, 7), CallSite(7, 8, 9)))

print("\n5.1 从短到长依次添加")
assert manager5.add_path(level1) == True
print_paths(manager5)

assert manager5.add_path(level2) == True
print_paths(manager5, "添加 level2 后")
assert level1 not in manager5.paths
print(f"✓ level2 替换 level1")

assert manager5.add_path(level3) == True
print_paths(manager5, "添加 level3 后")
assert level2 not in manager5.paths
print(f"✓ level3 替换 level2")

assert manager5.add_path(level4) == True
print_paths(manager5, "添加 level4 后")
assert level3 not in manager5.paths
print(f"✓ level4 替换 level3")

assert len(manager5.paths) == 1
assert level4 in manager5.paths
print(f"\n✓ 最终只保留最长路径")

# ============================================================================
# 测试 6: 实际场景模拟
# ============================================================================
print_section("测试 6: 实际调用路径场景")

manager6 = PathManager()

# 模拟实际的方法调用路径
call_path_1 = CallPath((
    CallSite(1, 10, 2),   # main -> foo
    CallSite(2, 20, 3),   # foo -> bar
    CallSite(3, 30, 4),   # bar -> baz
))

call_path_2 = CallPath((
    CallSite(1, 10, 2),   # main -> foo
    CallSite(2, 20, 3),   # foo -> bar
    CallSite(3, 35, 5),   # bar -> qux (不同的调用)
))

call_path_3 = CallPath((
    CallSite(1, 10, 2),   # main -> foo
    CallSite(2, 25, 6),   # foo -> helper (不同的调用)
))

print("\n6.1 添加三条实际调用路径")
assert manager6.add_path(call_path_1) == True
assert manager6.add_path(call_path_2) == True
assert manager6.add_path(call_path_3) == True

print_paths(manager6, "实际调用路径")
assert len(manager6.paths) == 3
print(f"\n✓ 三条不同的调用路径都保留")

print("\n6.2 尝试添加部分调用链")
partial = CallPath((
    CallSite(1, 10, 2),   # main -> foo
    CallSite(2, 20, 3),   # foo -> bar
))
assert manager6.add_path(partial) == False
print(f"✓ 部分调用链被拒绝（存在更完整的路径）")

# ============================================================================
# 总结
# ============================================================================
print_section("所有测试通过! ✓")
print(f"\n测试覆盖:")
print("  ✓ 不同分支路径可以共存")
print("  ✓ 同一分支只保留最长路径")
print("  ✓ 前缀路径被正确拒绝")
print("  ✓ 扩展路径可以替换前缀")
print("  ✓ 多层嵌套前缀正确处理")
print("  ✓ 边界情况处理正确")
print("  ✓ 实际场景模拟通过")