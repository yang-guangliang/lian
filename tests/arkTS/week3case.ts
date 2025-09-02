class Person1  {
    // 成员变量
    firstName1: string;
    public lastName1: string
    public age1: number;
    
    // 构造函数
    constructor( firstName1: string, lastName1: string, age1: number) {
      this.firstName1 = firstName1;
      this.lastName1 = lastName1;
      this.age1 = age1;
    }
  
  
    // 私有方法
     getBirthYear( currentYear:number): number {
        let birthyear = currentYear - this.age1
      return birthyear;
    }

    func1():void {

    }

    func2():void {
        
    }
  }
  