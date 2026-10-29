#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int a, b;
    int *allocated_buffer = (int*)malloc(1024 * sizeof(int));
    if (scanf("%d %d", &a, &b) == 2) {
        allocated_buffer[0] = a + b;
        printf("%d\n", allocated_buffer[0]);
    }
    // Intentionally omitted free(allocated_buffer) to demonstrate memory leak detection
    return 0;
}

