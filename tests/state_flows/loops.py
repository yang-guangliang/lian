def loops(flag):
    count = 0
    total = 0
            
    # While loop with break condition
    while flag and count < 10:
        count += 1
        if count == 5:
            break
        total += count
            
    return count, total
