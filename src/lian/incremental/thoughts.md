# structure
root -> src/lian/incremental

# how to refer

from lian.incremental import xxx

# gir

1. pause current task
2. call xxx.was_analyzed(unit_id, method_id)
3. if the target file/method exists, obtain its current content
4. Or, continue current task

# how to implement xxx.was_analyzed()
1. input: unit_id / method_id
2. output: loader
3. process:

- id -> locate the target file/method, loader
- read the target ..
- prepare the output format