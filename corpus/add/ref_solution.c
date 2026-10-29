#include <stdio.h>

int add_numbers(int first, int second) {
    return first + second;
}

int main(void) {
    int x, y;
    if (scanf("%d %d", &x, &y) == 2) {
        printf("%d\n", add_numbers(x, y));
    }
    return 0;
}

