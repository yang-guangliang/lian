## Avoid using fancy-style coding.

Example1:
```
results = [pool.apply_async(task, (file_unit,)) for file_unit in file_units]
```

It is hard to read, modify and maintain. Please consider a plain format:
```
results = []
for file_unit in file_units:
   new_thread = pool.apply_async(task, (file_unit,))
   results.append(new_thread)
```

Example2:
```
distance = sum(1 for i in range(length) if i >= len(components1) or i >= len(components2) or components1[i] != components2[i])
```

Using the following code instead.
```
distance = 0
for i in range(length):
    if i >= len(components1) or i >= len(components2) or components1[i] != components2[i]:
        distance += 1
```


## No Tab.

Only space is allowed.

## Avoid tuple

Tuple is hard to read. For example

```
defined_symbols.add((each_state, stmt_id, stmt_id))
```

Use class instead.
```
class SymbolDefNode:
    index:int = -1
    symbol_id:int = -1
    stmt_id: int = -1

defined_symbols.add(
    SymbolDefNode(index = each_state, symbol_id = stmt_id, stmt_id = stmt_id)
)
```

## Use meaningful variable name. Do not worry about variable length.

```
state_copy = self.create_state_copy(array_state)
```
VS
```
new_array_state = self.create_state_copy(array_state)
```

The second one "new_array_state" is preferred.

