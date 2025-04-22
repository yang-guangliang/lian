@global_var = global i32 0

@array = global [5 x i32] [i32 1, i32 2, i32 3, i32 4, i32 5]


%array.Myarray = type [5 x i32]

%struct.MyStruct = type { i32, [5 x i32] }
@my_struct = global %struct.MyStruct { i32 42, [5 x i32] [i32 1, i32 2, i32 3, i32 4, i32 5] }

%vector.type = type <5 x i32>
@my_vector = global %vector.type < i32 42, [5 x i32] [i32 1, i32 2, i32 3, i32 4, i32 5] >
