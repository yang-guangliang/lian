#!/usr/bin/env python3

import ast
from inspect import Parameter
import pprint

from networkx.generators.classic import complete_graph
from pandas.core import frame

from lian.core.resolver import Resolver
from lian.core.stmt_states import StmtStates
from lian.util import util
from lian.config import config
from lian.util.loader import Loader
# from lian.events.handler_template import AppTemplate
from lian.config.constants import (
    LIAN_SYMBOL_KIND,
    LIAN_INTERNAL,
    STATE_TYPE_KIND,
    LIAN_INTERNAL,
    CALLEE_TYPE,
    EVENT_KIND
)
from lian.common_structs import (
    CallGraph,
    CallSite,
    MethodDeclParameters,
    Parameter,
    Argument,
    MethodCallArguments,
    PathManager,
    StateDefNode,
    StmtStatus,
    Symbol,
    State,
    MethodCall,
    ComputeFrameStack,
    ComputeFrame,
    MethodSummaryTemplate,
    MethodSummaryInstance,
    SymbolStateSpace,
    SimpleWorkList,
    P2ResultFlag,
    MethodCallArguments,
    InterruptionData,
    CallPath,
    MethodDefUseSummary,
    SFGNode,
    SFGEdge,
    SFG_NODE_KIND,
    SFG_EDGE_KIND,
    CallRelevanceResult,
)
from lian.taint.rule_manager import RuleManager

class GlobalStmtStates(StmtStates):
    def __init__(
        self, analysis_phase_id, event_manager, loader: Loader, resolver: Resolver, compute_frame: ComputeFrame,
        path_manager: PathManager, caller_unknown_callee_edge: dict, complete_graph=None
    ):
        super().__init__(
            analysis_phase_id=analysis_phase_id,
            event_manager=event_manager,
            loader=loader,
            resolver=resolver,
            compute_frame=compute_frame,
            call_graph=None,
            complete_graph=complete_graph,
        )
        self.path_manager = path_manager
        self.caller_unknown_callee_edge = caller_unknown_callee_edge
        self._taint_rule_manager: RuleManager | None = None

    # def get_method_summary(self, method_id):
    #     pass

    # def has_been_analyzed(self, method_id):
    #     pass

    def print_path(self, path: tuple):
        if not path:
            return

        path_len = len(path)
        if path_len < 1:
            return

        path_str = f"{path[0]}"
        for i in range(3, len(path)+1, 2):
            path_str += f"-@-{path[i-2]}->-{path[i-1]}"

        print(f"current path: {path_str}")

    def _get_taint_rule_manager(self) -> RuleManager | None:
        """
        懒加载 RuleManager，供调用相关性判定逻辑使用。
        """
        if self._taint_rule_manager is not None:
            return self._taint_rule_manager
        options = getattr(self.loader, "options", None)
        default_settings = None
        if options is not None:
            default_settings = getattr(options, "default_settings", None)
        try:
            self._taint_rule_manager = RuleManager(default_settings)
        except Exception:
            self._taint_rule_manager = RuleManager()
        return self._taint_rule_manager

    def judge_call_relevance(
        self,
        stmt_id,
        stmt,
        status: StmtStatus,
        in_states,
        args: MethodCallArguments,
        defined_symbol,
        this_state_set: set[int],
        callee_method_ids: set[int] | None = None,
        name_symbol: Symbol | None = None,
    ) -> CallRelevanceResult:
        """
        基于 taint 规则和参数/receiver 的状态，判断当前调用在污点视角下是否“值得深入”。
        第一版实现尽量简单：优先看 taint 规则中的 name 命中情况，其次看参数/receiver 的访问路径。
        """
        # 仅在第三阶段 + 显式开启污点剪枝选项时生效
        loader = getattr(self, "loader", None)
        options = getattr(loader, "options", None) if loader is not None else None
        if (
            self.analysis_phase_id != ANALYSIS_PHASE_ID.GLOBAL_SEMANTICS
            or options is None
            or not getattr(options, "enable_p3_taint_guided", False)
        ):
            return CallRelevanceResult(is_relevant=True, reason="P3_TAINT_GUIDED_DISABLED")

        result = CallRelevanceResult(is_relevant=False, reason="INIT_IRRELEVANT")
        rule_manager = self._get_taint_rule_manager()
        lang = getattr(self, "lang", None)

        def _match_rule_name(rule_name: str, candidate: str) -> bool:
            if not rule_name or not candidate:
                return False
            if rule_name == candidate:
                return True
            return rule_name.endswith("." + candidate) or candidate.endswith("." + rule_name)

        # 1. 基于 callee 名称与 taint 规则的直接匹配（source/sink/propagation）
        callee_names: set[str] = set()
        if isinstance(name_symbol, Symbol) and util.is_available(getattr(name_symbol, "name", None)):
            callee_names.add(name_symbol.name)
        if isinstance(name_symbol, Symbol):
            for idx in getattr(name_symbol, "states", set()):
                if 0 <= idx < len(self.frame.symbol_state_space):
                    st = self.frame.symbol_state_space[idx]
                    if isinstance(st, State):
                        access_name = util.access_path_formatter(st.access_path)
                        if access_name:
                            callee_names.add(access_name)

        all_rules = []
        all_rules.extend(getattr(rule_manager, "all_sources", []))
        all_rules.extend(getattr(rule_manager, "all_sinks", []))
        all_rules.extend(getattr(rule_manager, "all_propagations", []))

        for candidate in callee_names:
            for rule in all_rules:
                if getattr(rule, "lang", None) not in (lang, config.ANY_LANG):
                    continue
                if _match_rule_name(getattr(rule, "name", None), candidate):
                    result.is_relevant = True
                    result.reason = "RULE_MATCH"
                    result.may_be_source = (getattr(rule, "kind", "") == "source")
                    return result

        # 2. 参数级相关性：检查参数/receiver 的访问路径是否命中 taint 规则
        tainted_arg_pos = []
        tainted_state_indexes = set()

        # 2.1 位置参数
        for pos, arg_set in enumerate(args.positional_args):
            for arg in arg_set:
                if not isinstance(arg, Argument):
                    continue
                access_path_str = util.access_path_formatter(arg.access_path)
                for rule in rule_manager.all_sources:
                    if getattr(rule, "lang", None) not in (lang, config.ANY_LANG):
                        continue
                    if _match_rule_name(getattr(rule, "name", None), access_path_str):
                        tainted_arg_pos.append(pos)
                        tainted_state_indexes.add(arg.index_in_space)
                        break

        # 2.2 命名参数
        for name, arg_set in args.named_args.items():
            for arg in arg_set:
                if not isinstance(arg, Argument):
                    continue
                access_path_str = util.access_path_formatter(arg.access_path)
                for rule in rule_manager.all_sources:
                    if getattr(rule, "lang", None) not in (lang, config.ANY_LANG):
                        continue
                    if _match_rule_name(getattr(rule, "name", None), access_path_str):
                        tainted_arg_pos.append(arg.position if arg.position >= 0 else -1)
                        tainted_state_indexes.add(arg.index_in_space)
                        break

        # 2.3 receiver（针对 object 调用或 this）
        for idx in this_state_set:
            if 0 <= idx < len(self.frame.symbol_state_space):
                st = self.frame.symbol_state_space[idx]
                if not isinstance(st, State):
                    continue
                access_path_str = util.access_path_formatter(st.access_path)
                for rule in rule_manager.all_sources:
                    if getattr(rule, "lang", None) not in (lang, config.ANY_LANG):
                        continue
                    if _match_rule_name(getattr(rule, "name", None), access_path_str):
                        result.may_have_side_effect = True
                        tainted_state_indexes.add(idx)
                        break

        if tainted_arg_pos or tainted_state_indexes:
            result.is_relevant = True
            result.reason = "TAINTED_ARG_OR_RECEIVER"
            result.relevant_arg_positions = tainted_arg_pos
            result.relevant_state_indexes = tainted_state_indexes
            return result

        # 其余情况认为与污点传播无关
        result.reason = "IRRELEVANT_BY_TAINT_RULES"
        return result

    def compute_target_method_states(
        self, stmt_id, stmt, status, in_states,
        callee_method_ids, target_symbol, args,
        this_state_set = set(), new_object_flag = False
    ):
        callee_ids_to_be_analyzed = []
        caller_id = self.frame.method_id
        if config.DEBUG_FLAG:
            util.debug(f"positional_args of stmt <{stmt_id}>: {args.positional_args}")
            util.debug(f"named_args of stmt <{stmt_id}>: {args.named_args}")
            util.debug(f"callee_method_ids: {callee_method_ids}")

        parameter_mapping_list = []

        if len(callee_method_ids) == 0:
            callee_name = self.resolver.recover_callee_name(stmt, status, self.frame.symbol_state_space)
            unknown_callee_set = self.caller_unknown_callee_edge.get(str(caller_id), set())
            unknown_callee_set.add((str(stmt_id), callee_name))
            self.caller_unknown_callee_edge[str(caller_id)] = unknown_callee_set

        for each_callee_id in callee_method_ids:
            new_call_site = CallSite(caller_id, stmt_id, each_callee_id)
            callee_path = self.frame.call_path.add_callsite(new_call_site)

            if(
                self.path_manager.path_exists(callee_path) or
                callee_path.count_cycles() > 1 or
                each_callee_id in self.frame.call_path or
                self.frame.content_already_analyzed.get(new_call_site, False) or
                self.frame.call_site_analyze_counter.get(new_call_site, 0) > config.MAX_ANALYSIS_ROUND_FOR_CALL_SITE
            ):
                continue
            self.frame.call_site_analyze_counter[new_call_site] = self.frame.call_site_analyze_counter.get(new_call_site, 0) + 1

            # 在第三阶段 + 污点剪枝模式下，对每个具体 callee 再做一次相关性判定；
            # 如果某个 callee 在 taint 视角下无关，则不压栈深入它。
            if self._taint_guided_p3_enabled():
                relevance = self.judge_call_relevance(
                    stmt_id,
                    stmt,
                    status,
                    in_states,
                    args,
                    target_symbol,
                    this_state_set,
                    {each_callee_id},
                    None,
                )
                if not relevance.is_relevant:
                    continue

            callee_ids_to_be_analyzed.append(each_callee_id)
            # prepare callee parameters
            # 可能第二阶段没有这个caller->callee，因此该call的parameter_list可能是空的，在这个阶段还是需要生成一遍parameter_list
            parameters = self.prepare_parameters(each_callee_id)
            if config.DEBUG_FLAG:
                util.debug(f"parameters of callee <{each_callee_id}>: {parameters}")
            # current_parameter_mapping_list = self.loader.load_parameter_mapping(new_call_site)
            # if util.is_empty(current_parameter_mapping_list):
            current_parameter_mapping_list = []
            self.map_arguments(args, parameters, current_parameter_mapping_list, new_call_site)
            parameter_mapping_list.extend(current_parameter_mapping_list)

        classes_of_method = []
        for index in this_state_set:
            instance_state = self.frame.symbol_state_space[index]
            if isinstance(instance_state, State) and self.is_state_a_class_decl(instance_state):
                classes_of_method.append(instance_state.value)

        if len(callee_ids_to_be_analyzed) != 0:
            # print(f"callee_ids_to_be_analyzed: {callee_ids_to_be_analyzed}")
            this_class_ids = []
            name_symbol_index = status.used_symbols[0]
            name_symbol = self.frame.symbol_state_space[name_symbol_index]
            for name_state_index in name_symbol.states:
                name_state = self.frame.symbol_state_space[name_state_index]
                if isinstance(name_state, State) and self.is_state_a_class_decl(name_state):
                   this_class_ids.append(name_state.value)

            return P2ResultFlag(
                # states_changed = True,
                # defuse_changed = defuse_changed,
                interruption_flag = True,
                interruption_data = InterruptionData(
                    caller_id = self.frame.method_id,
                    call_stmt_id = stmt_id,
                    callee_ids = callee_ids_to_be_analyzed,
                    args_list = parameter_mapping_list,
                    classes_of_method = classes_of_method,
                    this_class_ids = this_class_ids,
                ),
            )

        for each_callee_id in callee_method_ids:
            new_call_site = CallSite(caller_id, stmt_id, each_callee_id)
            self.frame.call_site_analyze_counter[new_call_site] = self.frame.call_site_analyze_counter.get(new_call_site, 0) + 1
            if caller_id != each_callee_id:
                new_path = self.frame.call_path.add_callsite(new_call_site)
                self.path_manager.add_path(new_path)
            # prepare callee summary instance and compact space
            callee_summary = self.loader.get_method_summary_instance(new_call_site.hash())
            if callee_summary:
                callee_summary = callee_summary.copy()
                self.apply_callee_semantic_summary(
                    stmt_id, stmt, each_callee_id, args, callee_summary,
                    self.frame.symbol_state_space, this_state_set, new_object_flag
                )

        return P2ResultFlag()

    def parameter_decl_stmt_state(self, stmt_id, stmt, status: StmtStatus, in_states):
        parameter_name_symbol = self.frame.symbol_state_space[status.defined_symbol]
        symbol_id = parameter_name_symbol.symbol_id
        if isinstance(parameter_name_symbol, Symbol) and self.frame.params_list:
            parameter_name_symbol.states = set()
            for each_pair in self.frame.params_list:
                if each_pair.parameter_symbol_id == symbol_id:
                    parameter_state_index = each_pair.arg_index_in_space
                    # self.update_access_path_state_id(parameter_state_index)
                    parameter_name_symbol.states.add(parameter_state_index)
                    status.defined_states.add(parameter_state_index)
                    self.add_arg_to_param_edge(each_pair, status, parameter_name_symbol)

            if len(status.used_symbols) > 0:
                default_value_index = status.used_symbols[0]
                default_value = self.frame.symbol_state_space[default_value_index]
                if isinstance(default_value, Symbol):
                    value_state_indexes = self.read_used_states(default_value_index, in_states)
                    for default_value_state_index in value_state_indexes:
                        # self.tag_key_state_flag(stmt_id, default_value.symbol_id, default_value_state_index)
                        util.add_to_dict_with_default_set(
                            self.frame.method_summary_template.used_external_symbols,
                            default_value.symbol_id,
                            [default_value_state_index]
                        )

                else:
                    parameter_name_symbol.states.add(default_value_index)
        return P2ResultFlag()

    def is_used_in_call_stmt(self, sfg_node):
        children = list(self.sfg.graph.successors(sfg_node))
        for child in children:
            if (
                child.node_type == SFG_NODE_KIND.STMT
                and self.loader.get_stmt_gir(child.def_stmt_id).operation in ["call_stmt", "object_call_stmt"]
            ):
                return True
        return False

    def add_arg_to_param_edge(self, each_pair, status, parameter_name_symbol):
        for node in self.sfg.graph.nodes:
            if self.node_is_state(node) and node.index == each_pair.arg_index_in_space:
                # `node` 是参数对应的 STATE 节点；它的直接前驱通常是 SYMBOL。
                # 但在某些建图路径下，可能出现 STATE -> STATE 的链路（如 inclusion/copy），
                # 导致直接前驱里包含 STATE 节点。此时需要把这些 STATE 的父 SYMBOL 也纳入候选，
                # 以便找到真正“在 call_stmt/object_call_stmt 中被使用”的变量节点。
                all_parent_nodes = set(self.sfg.graph.predecessors(node))
                for parent in list(all_parent_nodes):
                    if getattr(parent, "node_type", None) != SFG_NODE_KIND.STATE:
                        continue
                    for pp in self.sfg.graph.predecessors(parent):
                        if getattr(pp, "node_type", None) == SFG_NODE_KIND.SYMBOL:
                            all_parent_nodes.add(pp)

                all_parent_nodes = list(all_parent_nodes)
                for parent_node in all_parent_nodes:
                    if not self.is_used_in_call_stmt(parent_node):
                        continue
                    self.sfg.add_edge(
                        parent_node,
                        SFGNode(
                            node_type=SFG_NODE_KIND.SYMBOL,
                            def_stmt_id=parameter_name_symbol.stmt_id,
                            index=status.defined_symbol,
                            node_id=parameter_name_symbol.symbol_id,
                            name=parameter_name_symbol.name,
                            context=self.frame.get_context(),
                        ),
                        SFGEdge(
                            edge_type=SFG_EDGE_KIND.SYMBOL_FLOW,
                            stmt_id=parameter_name_symbol.stmt_id
                        )
                    )
                    break
