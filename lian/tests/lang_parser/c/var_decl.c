int main() {
    
    //变量声明
    //int c,d,e,f,g,h,j,k;
    //常量声明
    const int i = 0;
    //一维数组声明
    int cc = 0;
    int arr[3];
    int brr[2] = {5, 6};
    int crr[] = {1, 2, cc + 1};
    //指针声明
    /* int *p, **p1; */
    //常量数组声明
    /* const int carr[2] = {1, 2}; */
    //多维数组声明
    /* int arr[2][3][4] = {
        { 
            {1, 2, 3, 4}, 
            {5, 6, 7, 8}, 
            {9, 10, 11, 12}  
        },
        { 
            {13, 14, 15, 16},
            {17, 18, 19, 20}, 
            {21, 22, 23, 24}  
        }
    }; */
    /* int arr[][][] = {
        { 
            {1, 2, 3, 4}, 
            {5, 6, 7, 8}, 
            {9, 10, 11, 12}  
        },
        { 
            {13, 14, 15, 16},
            {17, 18, 19, 20}, 
            {21, 22, 23, 24}  
        }
    }; */
    /* int arr[2][3][4]; */
    //const指针
    /* int * const p = a;
    const int *q = a;
    const int * const p1 = a; */
    //enum类型
    /* enum{
        a,
        b=3,
        c
    }abc=a; */
    //struct定义
    /*  struct Grade {
        int math,*english,*physics[3][2];
        int chinese[5];
        const int TOTAL_SUBJECTS;
    }grade;
    */
    /* struct ABC {
        int Integer;
        char c;
    };

    struct ABC abc; */

    //带初值
    /* struct ABC {
        int num;
        char letter;
    };
    struct ABC abc = {1, 'a'}; */
    //要不要考虑初始化值少于成员数量的情况？要
    /* struct ABC {
        int num;
        char letter;
    };
    struct ABC abc = {1}; */
    //结构体数组
    /* struct Person {
        char name[50];
        int age;
    };
    struct Person people[3] = {
        {"Alice", 30},
        {"Bob", 25},
        {"Charlie", 28}
    }; */

    //以field_designator赋值
    /* struct ABC {
        int Integer;
        char c;
    }abc = {
        .c= 'a',
        .Integer = 1,
    }; */
    /* struct ABC {
        int Integer;
        char c;
    }abc = {1,'a'},def = {2,'b'}; */

    //不带name
    /* struct{
        int Integer;
        char c;
    }abc = {1,'a'}; */
    //union 定义与声明
    /* union ABC {
        int Integer;
        char c;
    }abc = {1,'a'},def = {2,'b'}; */

    // float aa;
    /* int a = 50;
    float b = 60;
    //int a[]={10};
    unsigned int a[] = {10}, b = 20; 
    /*int a = 10,b[]={10,20}, *p=5, (d)=114,e,f; */
}