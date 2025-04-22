pub union Person<T> where T:Debug{
    name: T,
    age: i32,
    pub height: f32,
}