def cfg_try():
    try:
        number = int(input("Enter a number: "))
        result = 10 / number
    except ValueError as VE:
        print("Please enter a valid integer.")
    except ValueError as VE:
        print("Please enter a valid integer.")
    except:
        print("Cannot divide by zero!")
    else:
        print("Result:", result)
    finally:
        print("This block is executed no matter what.")