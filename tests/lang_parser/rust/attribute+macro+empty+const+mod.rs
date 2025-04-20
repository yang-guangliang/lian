#![allow(dead_code)]

macro_rules! complex_macro {
    ($name:ident, $val:expr) => {
        let $name = $val;
        println!("{} = {}", stringify!($name), $name);
    };
}

fn main() {
    complex_macro!(x, 10);
    complex_macro!(y, 20 * 2);
}

;

pub const PUBLIC_CONST: i32 = 100;

pub mod my_module {
    pub const PUBLIC_CONST: i32 = 100;
}
