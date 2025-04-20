pub unsafe trait MyTrait<T, U>: Sized + Send + Sync
    where
        T: Clone + Debug,
        U: PartialEq + Eq,
    {
        type Output; // 关联类型
    
        fn new(value: T) -> Self; // 关联函数
    
        fn process(&self, item: &U) -> Self::Output; // 方法
    
        const CONSTANT: i32; // 关联常量
    
        impl Sized for MyTrait<T, U> {} // 内嵌的impl块
}
