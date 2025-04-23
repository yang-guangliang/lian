# tests/example.py
def callee(a):
    b = a["x"]
    #vulnerable_function
    b["func"] = lambda x : print("vulnerable")
    
o = {
    "x" : {}
}

def caller():
    p = o["x"]
    # benign_function
    p["func"] = lambda x : print("benign")
    callee(o)
    target = p["func"]
    target()

caller()

