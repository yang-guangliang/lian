
    OuterLoop:
    for i := 0; i < 5; i++ {
        for j := 0; j < 5; j++ {
            if j == 2 {
                continue OuterLoop 
            }
            fmt.Printf("i = %d, j = %d\n", i, j)
        }
    }

    
    {
        fmt.Println("This is a block statement")
    }

    
    ; 

    
    fmt.Println("Before goto")
    goto Skip
    fmt.Println("This will not be executed")
    Skip:
    fmt.Println("After goto")

BlockLabel:
    {
        fmt.Println("This is a labeled block")
        goto BlockLabel 
    }
