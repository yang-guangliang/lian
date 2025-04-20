a = 3


def outer_function():
    def inner_function(x, y): # def (inner_function state:[2])
        return a(x, y)
    def operation(a, b): # def (operation state:[4])
        return a * b
    a = operation # def (a state:[4])
    result = inner_function(10, 5) # inbits:[2,4,6]
    return result

result = outer_function()
print("Result:", result)  # 输出: Result: 50

'''
first round:    stack: outer_function
outer_function:
2. method_decl  <def (inner_function state:[2])>    inbits:0
4. method_decl  <def (operation state:[4])>         inbits:2
6. assign       <def (a state:[4])>                 inbits:2,4
7. call         <def result>                        inbits:2,4,6
    get callee_name => inner_function
    get states      => 2 from 2
    call(2)

second round:   stack: outer_function, inner_function
inner_function:
3. call         <def %v>  
    get callee_name => a                          
'''
