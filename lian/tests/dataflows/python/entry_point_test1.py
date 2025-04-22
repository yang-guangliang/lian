a = 3

def plusOne():
    global a 
    a += 1

def func(x):
    x = x + 1

if __name__ == "__main__":
    print("global_analysis_test")
    plusOne()
    print(a)

