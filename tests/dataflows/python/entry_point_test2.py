b = 1000

def miunsOne():
    global b 
    b -= 1

def func1(x):
    x = x + 1

if __name__ == "__main__":
    print("global_analysis_test2")

    # call
    miunsOne()
    print(b)

