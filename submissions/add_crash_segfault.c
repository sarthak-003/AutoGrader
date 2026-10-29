#include <stdio.h>

int main(void) {
    int a, b;
    scanf("%d %d", &a, &b);
    int *null_ptr = NULL;
    *null_ptr = 999; // Explicit Null pointer dereference / crash
    printf("%d\n", a + b);
    return 0;
}

