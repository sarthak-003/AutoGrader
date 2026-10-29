#include <stdio.h>
#include <stdlib.h>

int main() {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int *a = (int*)malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);
    int t;
    if (scanf("%d", &t) != 1) { free(a); return 0; }
    
    // Inefficient O(N^2) brute-force nested loops
    int f = 0;
    for (int i = 0; i < n; i++) {
        for (int j = i + 1; j < n; j++) {
            if (a[i] + a[j] == t) {
                printf("%d %d\n", i, j);
                f = 1;
                break;
            }
        }
        if (f) break;
    }
    if (!f) printf("-1\n");
    
    free(a);
    return 0;
}

