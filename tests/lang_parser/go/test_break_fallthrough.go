  switch i := 2; i {
    case 2:
        fmt.Println("Two")
        fallthrough
    case 3:
        fmt.Println("Three")
        break
      }
  for i := 0; i < 10; i++ {
        if i > 5 {
            break
        }
        fmt.Println(i)
   }
