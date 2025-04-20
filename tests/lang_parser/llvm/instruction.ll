@global_var = global i32 0
@array = global [5 x i32] [i32 1, i32 2, i32 3, i32 4, i32 5]
define void @main() {
entry:
  %new_struct = insertvalue %MyStruct %struct, i32 %new_value, 0
  %caught = landingpad { i8*, i32 } 
  %result = phi i32 [ 1, %if_true ], [ 0, %if_false ]
  switch i32 %value, label %default_case [
    i32 1, label %case1
    i32 2, label %case2
    i32 3, label %case3
  ]

  %cmp = icmp slt i32 %x, 10
  br i1 %cmp, label %if_true, label %if_false
  %casted_value = trunc i64 %a to i32
  %casted_value = fpext float %a to double
  %cmp = icmp eq i32 %a, %b
  <result> = callbr i32 asm "", "=r,r,!i"(i32 %x)
            to label %fallthrough [label %indirect]
  invoke void @someFunction(i32 %x) to label %normal unwind label %exceptionHandler
  %call = call dereferenceable(4) void @foo(i32 %a dereferenceable(4), i32 %b align 4, i32 %c)
  br label %next_block
  br i1 %cond, label %true_block, label %false_block
  %ptr = alloca i32, i32 %size
  %zero = alloca i32
  %result = call void (i32*)* @bar(i32* %ptr) align 4
  %local_var = alloca i32
  store i32 42, i32* @global_var, align 4
  %loaded_value = load i32, i32* @global_var, align 4
  call void @print(i32 %loaded_value)
  store i32 100, i32* %local_var, align 4
  %loaded_local = load i32, i32* %local_var, align 4
  call void @print(i32 %loaded_local)
  ret void
}

declare void @print(i32)

@global_var = global i32 0