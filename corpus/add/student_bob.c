#include <stdio.h>

int main(void) {
    long long n1, n2;
    if (scanf("%lld %lld", &n1, &n2) == 2) {
        printf("%lld\n", n1 + n2);
    }
    return 0;
}

