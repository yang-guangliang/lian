#include <stdio.h>

int a = 3;

int main(int argc, char **argv)
{
    int a = 4;

{
    int a = 5;
}

    printf(a);

	return 0;
}
