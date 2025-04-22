int (__cdecl my_function)(int a, float b, ...) 
    __asm__("eax") 
    __attribute__((noreturn));

int (__cdecl my_function)(int a, float b, ...) 
    __asm__("eax") 
    __attribute__((noreturn)) 
    my_attribute 
    some_macro_call(1, 2) = { };