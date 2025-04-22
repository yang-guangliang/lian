# tests/example.py
def bar(a):
    b = a["x"]
    #vulnerable_function
    b["func"] = lambda x : print("vulnerable")
    
o = {
    "x" : {}
}

def main():
    p = o["x"]
    # benign_function
    p["func"] = lambda x : print("benign")
    bar(o)
    target = p["func"]
    target()

main()



