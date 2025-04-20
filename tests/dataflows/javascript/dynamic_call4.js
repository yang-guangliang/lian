class User {
    getName() {   
        return "dilo";
    }
}

user = new User();
dynamicMethod = 'getName';
a = user[dynamicMethod](); //dilo
