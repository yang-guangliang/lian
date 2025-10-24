#! /usr/bin/env python3

from taint_manager import TaintManager

class TaintAnalysis:
    def __init__(self, lian, options, loader):
        self.options = options
        self.lian = lian
        self.loader = loader
        self.taint_manager = TaintManager(self.lian, self.loader)

    def find_sources(self, sfg, ct):
        node_list = []
        # 应该包括所有的可能symbol和state节点作为sources
        # 这里应该应用source的规则
        return node_list

    def find_sinks(self, sfg, ct):
        # 找到所有的sink函数或者语句
        # 这里应该应用sink的规则
        node_list = []
        return node_list

    def find_flows(self, sfg, ct, sources, sinks):
        # 找到所有的taint flow
        # 这里需要应用图遍历算法对taint进行传播
        # 这里需要把taint管理器用起来，对symbol和state层面有污点的节点进行标记
        flow_list = []
        for source in sources:
            for sink in sinks:
                if sfg.has_edge(source, sink):
                    flow_list.append((source, sink))
        return flow_list

    def run(self, entry_point):
        for entry_point in self.loader.get_entry_points():
            call_tree = self.loader.get_call_tree(entry_point)
            sfg = self.loader.get_sfg(entry_point)

            sources = self.find_sources(sfg, call_tree)
            sinks = self.find_sinks(sfg, call_tree)
            flows = self.find_flows(sfg, call_tree, sources, sinks)