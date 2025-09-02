#include <stdio.h>
int main() {
    // int a, c;
    char aaa = 'x';        
    int *p;     
    int **q;        
    int d;      
    if(1){      
        int a = 3;  
        p = &a; 
                
    }
    else{
        int a = 4;    
        p = &a; 
                
    }
    int c = *p;               
    q = &p;
    int *t = &a;
    int z = *t;
    d = **q;   
    d = *p;           
    return 0;
}
int a=1;
