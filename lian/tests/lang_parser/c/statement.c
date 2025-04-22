switch (a++) {
    case 0:
        a++;
        break;

    default:
        a--;
        break;
}
/*
[{'assign_stmt': {'target': '%v0', 'operand': 'a'}},
 {'assign_stmt': {'target': 'a',
                  'operator': '+',
                  'operand': 'a',
                  'operand2': '1'}},
 {'switch_stmt': {'condition': '%v0',
                  'body': [{'case_stmt': {'condition': '0',
                                          'body': [{'assign_stmt': {'target': '%v0',
                                                                    'operand': 'a'}},
                                                   {'assign_stmt': {'target': 'a',
                                                                    'operator': '+',
                                                                    'operand': 'a',
                                                                    'operand2': '1'}},
                                                   {'break_stmt': {'target': ''}}]}},
                           {'default_stmt': {'body': [{'assign_stmt': {'target': '%v0',
                                                                       'operand': 'a'}},
                                                      {'assign_stmt': {'target': 'a',
                                                                       'operator': '-',
                                                                       'operand': 'a',
                                                                       'operand2': '1'}},
                                                      {'break_stmt': {'target': ''}}]}}]}}]
[{'operation': 'assign_stmt', 'stmt_id': 1, 'target': '%v0', 'operand': 'a'},
 {'operation': 'assign_stmt',
  'stmt_id': 2,
  'target': 'a',
  'operator': '+',
  'operand': 'a',
  'operand2': '1'},
 {'operation': 'switch_stmt', 'stmt_id': 3, 'condition': '%v0', 'body': 4},
 {'operation': 'block_start', 'stmt_id': 4, 'parent_stmt_id': 3},
 {'operation': 'case_stmt', 'stmt_id': 5, 'condition': '0', 'body': 6},
 {'operation': 'block_start', 'stmt_id': 6, 'parent_stmt_id': 5},
 {'operation': 'assign_stmt', 'stmt_id': 7, 'target': '%v0', 'operand': 'a'},
 {'operation': 'assign_stmt',
  'stmt_id': 8,
  'target': 'a',
  'operator': '+',
  'operand': 'a',
  'operand2': '1'},
 {'operation': 'break_stmt', 'stmt_id': 9, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 6, 'parent_stmt_id': 5},
 {'operation': 'default_stmt', 'stmt_id': 10, 'body': 11},
 {'operation': 'block_start', 'stmt_id': 11, 'parent_stmt_id': 10},
 {'operation': 'assign_stmt', 'stmt_id': 12, 'target': '%v0', 'operand': 'a'},
 {'operation': 'assign_stmt',
  'stmt_id': 13,
  'target': 'a',
  'operator': '-',
  'operand': 'a',
  'operand2': '1'},
 {'operation': 'break_stmt', 'stmt_id': 14, 'target': ''},
 {'operation': 'block_end', 'stmt_id': 11, 'parent_stmt_id': 10},
 {'operation': 'block_end', 'stmt_id': 4, 'parent_stmt_id': 3}]
*/
{
    loop_start:
        if(i>=5) goto loop_end;
        printf("%d ", i);
        i++;
        goto loop_start;

    loop_end:
        return 0
}
/*
[{'label_stmt': {'name': 'loop_start'}},
 {'assign_stmt': {'target': '%v0',
                  'operator': '>=',
                  'operand': 'i',
                  'operand2': '5'}},
 {'if_stmt': {'condition': '%v0',
              'then_body': [{'goto_stmt': {'target': 'loop_end'}}]}},
 {'call_stmt': {'target': '%v1', 'name': 'printf', 'args': ['"%d "', 'i']}},
 {'assign_stmt': {'target': '%v2', 'operand': 'i'}},
 {'assign_stmt': {'target': 'i',
                  'operator': '+',
                  'operand': 'i',
                  'operand2': '1'}},
 {'goto_stmt': {'target': 'loop_start'}}, {'label_stmt': {'name': 'loop_end'}},
 {'return_stmt': {'target': '0'}}]
[{'operation': 'label_stmt', 'stmt_id': 1, 'name': 'loop_start'},
 {'operation': 'assign_stmt',
  'stmt_id': 2,
  'target': '%v0',
  'operator': '>=',
  'operand': 'i',
  'operand2': '5'},
 {'operation': 'if_stmt', 'stmt_id': 3, 'condition': '%v0', 'then_body': 4},
 {'operation': 'block_start', 'stmt_id': 4, 'parent_stmt_id': 3},
 {'operation': 'goto_stmt', 'stmt_id': 5, 'target': 'loop_end'},
 {'operation': 'block_end', 'stmt_id': 4, 'parent_stmt_id': 3},
 {'operation': 'call_stmt',
  'stmt_id': 6,
  'target': '%v1',
  'name': 'printf',
  'args': '[\'"%d "\', \'i\']'},
 {'operation': 'assign_stmt', 'stmt_id': 7, 'target': '%v2', 'operand': 'i'},
 {'operation': 'assign_stmt',
  'stmt_id': 8,
  'target': 'i',
  'operator': '+',
  'operand': 'i',
  'operand2': '1'},
 {'operation': 'goto_stmt', 'stmt_id': 9, 'target': 'loop_start'},
 {'operation': 'label_stmt', 'stmt_id': 10, 'name': 'loop_end'},
 {'operation': 'return_stmt', 'stmt_id': 11, 'target': '0'}]
*/

while(a++, b>0){
    b--;
}
/*
[{'assign_stmt': {'target': '%v0', 'operand': 'a'}},
 {'assign_stmt': {'target': 'a',
                  'operator': '+',
                  'operand': 'a',
                  'operand2': '1'}},
 {'assign_stmt': {'target': '%v1',
                  'operator': '>',
                  'operand': 'b',
                  'operand2': '0'}},
 {'while_stmt': {'condition': '%v1',
                 'body': [{'assign_stmt': {'target': '%v0', 'operand': 'b'}},
                          {'assign_stmt': {'target': 'b',
                                           'operator': '-',
                                           'operand': 'b',
                                           'operand2': '1'}},
                          {'assign_stmt': {'target': '%v0', 'operand': 'a'}},
                          {'assign_stmt': {'target': 'a',
                                           'operator': '+',
                                           'operand': 'a',
                                           'operand2': '1'}},
                          {'assign_stmt': {'target': '%v1',
                                           'operator': '>',
                                           'operand': 'b',
                                           'operand2': '0'}}]}}]
[{'operation': 'assign_stmt', 'stmt_id': 1, 'target': '%v0', 'operand': 'a'},
 {'operation': 'assign_stmt',
  'stmt_id': 2,
  'target': 'a',
  'operator': '+',
  'operand': 'a',
  'operand2': '1'},
 {'operation': 'assign_stmt',
  'stmt_id': 3,
  'target': '%v1',
  'operator': '>',
  'operand': 'b',
  'operand2': '0'},
 {'operation': 'while_stmt', 'stmt_id': 4, 'condition': '%v1', 'body': 5},
 {'operation': 'block_start', 'stmt_id': 5, 'parent_stmt_id': 4},
 {'operation': 'assign_stmt', 'stmt_id': 6, 'target': '%v0', 'operand': 'b'},
 {'operation': 'assign_stmt',
  'stmt_id': 7,
  'target': 'b',
  'operator': '-',
  'operand': 'b',
  'operand2': '1'},
 {'operation': 'assign_stmt', 'stmt_id': 8, 'target': '%v0', 'operand': 'a'},
 {'operation': 'assign_stmt',
  'stmt_id': 9,
  'target': 'a',
  'operator': '+',
  'operand': 'a',
  'operand2': '1'},
 {'operation': 'assign_stmt',
  'stmt_id': 10,
  'target': '%v1',
  'operator': '>',
  'operand': 'b',
  'operand2': '0'},
 {'operation': 'block_end', 'stmt_id': 5, 'parent_stmt_id': 4}]
*/

 for (int i = 1, j = 1; i <= n && j + 1 <= 1; i = j + 1, k++) {
     a = b + 1;
     continue;
 }


// [{'for_stmt': {'init_body': [],
//                'condition_prebody': [{'assign_stmt': {'target': '%v0',
//                                                       'operator': '<=',
//                                                       'operand': 'i',
//                                                       'operand2': 'n'}},
//                                      {'assign_stmt': {'target': '%v1',
//                                                       'operator': '+',
//                                                       'operand': 'j',
//                                                       'operand2': '1'}},
//                                      {'assign_stmt': {'target': '%v2',
//                                                       'operator': '<=',
//                                                       'operand': '%v1',
//                                                       'operand2': '1'}},
//                                      {'assign_stmt': {'target': '%v3',
//                                                       'operator': '&&',
//                                                       'operand': '%v0',
//                                                       'operand2': '%v2'}}],
//                'condition': '%v3',
//                'update_body': [{'assign_stmt': {'target': '%v0',
//                                                 'operator': '+',
//                                                 'operand': 'j',
//                                                 'operand2': '1'}},
//                                {'assign_stmt': {'target': 'i',
//                                                 'operand': '%v0'}},
//                                {'assign_stmt': {'target': '%v1',
//                                                 'operand': 'k'}},
//                                {'assign_stmt': {'target': 'k',
//                                                 'operator': '+',
//                                                 'operand': 'k',
//                                                 'operand2': '1'}}],
//                'body': [{'assign_stmt': {'target': '%v0',
//                                          'operator': '+',
//                                          'operand': 'b',
//                                          'operand2': '1'}},
//                         {'assign_stmt': {'target': 'a', 'operand': '%v0'}},
//                         {'continue_stmt': {'target': ''}}]}}]
// [{'operation': 'for_stmt',
//   'stmt_id': 1,
//   'init_body': None,
//   'condition_prebody': 2,
//   'condition': '%v3',
//   'update_body': 7,
//   'body': 12},
//  {'operation': 'block_start', 'stmt_id': 2, 'parent_stmt_id': 1},
//  {'operation': 'assign_stmt',
//   'stmt_id': 3,
//   'target': '%v0',
//   'operator': '<=',
//   'operand': 'i',
//   'operand2': 'n'},
//  {'operation': 'assign_stmt',
//   'stmt_id': 4,
//   'target': '%v1',
//   'operator': '+',
//   'operand': 'j',
//   'operand2': '1'},
//  {'operation': 'assign_stmt',
//   'stmt_id': 5,
//   'target': '%v2',
//   'operator': '<=',
//   'operand': '%v1',
//   'operand2': '1'},
//  {'operation': 'assign_stmt',
//   'stmt_id': 6,
//   'target': '%v3',
//   'operator': '&&',
//   'operand': '%v0',
//   'operand2': '%v2'},
//  {'operation': 'block_end', 'stmt_id': 2, 'parent_stmt_id': 1},
//  {'operation': 'block_start', 'stmt_id': 7, 'parent_stmt_id': 1},
//  {'operation': 'assign_stmt',
//   'stmt_id': 8,
//   'target': '%v0',
//   'operator': '+',
//   'operand': 'j',
//   'operand2': '1'},
//  {'operation': 'assign_stmt', 'stmt_id': 9, 'target': 'i', 'operand': '%v0'},
//  {'operation': 'assign_stmt', 'stmt_id': 10, 'target': '%v1', 'operand': 'k'},
//  {'operation': 'assign_stmt',
//   'stmt_id': 11,
//   'target': 'k',
//   'operator': '+',
//   'operand': 'k',
//   'operand2': '1'},
//  {'operation': 'block_end', 'stmt_id': 7, 'parent_stmt_id': 1},
//  {'operation': 'block_start', 'stmt_id': 12, 'parent_stmt_id': 1},
//  {'operation': 'assign_stmt',
//   'stmt_id': 13,
//   'target': '%v0',
//   'operator': '+',
//   'operand': 'b',
//   'operand2': '1'},
//  {'operation': 'assign_stmt', 'stmt_id': 14, 'target': 'a', 'operand': '%v0'},
//  {'operation': 'continue_stmt', 'stmt_id': 15, 'target': ''},
//  {'operation': 'block_end', 'stmt_id': 12, 'parent_stmt_id': 1}]

return a,k+c,d;
/*
[{'assign_stmt': {'target': '%v0',
                  'operator': '+',
                  'operand': 'k',
                  'operand2': 'c'}},
 {'return_stmt': {'target': 'd'}}]
[{'operation': 'assign_stmt',
  'stmt_id': 1,
  'target': '%v0',
  'operator': '+',
  'operand': 'k',
  'operand2': 'c'},
 {'operation': 'return_stmt', 'stmt_id': 2, 'target': 'd'}]
*/

{
     __try
    {
        puts(" in try2 ");
        __try
        {
            puts(" in try3 "); 
            * p = 13;  //导致一个存储异常 
            puts(" 这里不会被执行到 ");
        }
         __finally
        {
            puts(" in finally ");
        }
        puts(" 这里也不会被执行到 ");
    }
__finally
    {
        a++;
    }

}
/*
[{'try_stmt': {'body': [{'call_stmt': {'target': '%v0',
                                       'name': 'puts',
                                       'args': ['" in try2 "']}},
                        {'try_stmt': {'body': [{'call_stmt': {'target': '%v0',
                                                              'name': 'puts',
                                                              'args': ['" in '
                                                                       'try3 '
                                                                       '"']}},
                                               {'mem_write': {'address': 'p',
                                                              'source': '13'}},
                                               {'mem_read': {'target': '%v1',
                                                             'address': 'p'}},
                                               {'call_stmt': {'target': '%v2',
                                                              'name': 'puts',
                                                              'args': ['" '
                                                                       '这里不会被执行到 '
                                                                       '"']}}],
                                      'catch_body': [],
                                      'final_body': [{'call_stmt': {'target': '%v0',
                                                                    'name': 'puts',
                                                                    'args': ['" '
                                                                             'in '
                                                                             'finally '
                                                                             '"']}}]}},
                        {'call_stmt': {'target': '%v1',
                                       'name': 'puts',
                                       'args': ['" 这里也不会被执行到 "']}}],
               'catch_body': [],
               'final_body': [{'assign_stmt': {'target': '%v0',
                                               'operand': 'a'}},
                              {'assign_stmt': {'target': 'a',
                                               'operator': '+',
                                               'operand': 'a',
                                               'operand2': '1'}}]}}]
[{'operation': 'try_stmt',
  'stmt_id': 1,
  'body': 2,
  'catch_body': None,
  'final_body': 13},
 {'operation': 'block_start', 'stmt_id': 2, 'parent_stmt_id': 1},
 {'operation': 'call_stmt',
  'stmt_id': 3,
  'target': '%v0',
  'name': 'puts',
  'args': '[\'" in try2 "\']'},
 {'operation': 'try_stmt',
  'stmt_id': 4,
  'body': 5,
  'catch_body': None,
  'final_body': 10},
 {'operation': 'block_start', 'stmt_id': 5, 'parent_stmt_id': 4},
 {'operation': 'call_stmt',
  'stmt_id': 6,
  'target': '%v0',
  'name': 'puts',
  'args': '[\'" in try3 "\']'},
 {'operation': 'mem_write', 'stmt_id': 7, 'address': 'p', 'source': '13'},
 {'operation': 'mem_read', 'stmt_id': 8, 'target': '%v1', 'address': 'p'},
 {'operation': 'call_stmt',
  'stmt_id': 9,
  'target': '%v2',
  'name': 'puts',
  'args': '[\'" 这里不会被执行到 "\']'},
 {'operation': 'block_end', 'stmt_id': 5, 'parent_stmt_id': 4},
 {'operation': 'block_start', 'stmt_id': 10, 'parent_stmt_id': 4},
 {'operation': 'call_stmt',
  'stmt_id': 11,
  'target': '%v0',
  'name': 'puts',
  'args': '[\'" in finally "\']'},
 {'operation': 'block_end', 'stmt_id': 10, 'parent_stmt_id': 4},
 {'operation': 'call_stmt',
  'stmt_id': 12,
  'target': '%v1',
  'name': 'puts',
  'args': '[\'" 这里也不会被执行到 "\']'},
 {'operation': 'block_end', 'stmt_id': 2, 'parent_stmt_id': 1},
 {'operation': 'block_start', 'stmt_id': 13, 'parent_stmt_id': 1},
 {'operation': 'assign_stmt', 'stmt_id': 14, 'target': '%v0', 'operand': 'a'},
 {'operation': 'assign_stmt',
  'stmt_id': 15,
  'target': 'a',
  'operator': '+',
  'operand': 'a',
  'operand2': '1'},
 {'operation': 'block_end', 'stmt_id': 13, 'parent_stmt_id': 1}]
*/