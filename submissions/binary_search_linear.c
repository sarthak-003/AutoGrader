#include <stdio.h>
#include <stdlib.h>

int main() {
    int n;
    if (scanf("%d", &n) != 1) return 0;
    int *a = (int*)malloc(n * sizeof(int));
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);
    int t;
    if (scanf("%d", &t) != 1) { free(a); return 0; }
    
    // Buggy algorithmic design: O(N) linear scan instead of O(log N) binary search
    int found_idx = -1;
    for (int i = 0; i < n; i++) {
        if (a[i] == t) {
            found_idx = i;
            break;
        }
    }
    printf("%d\n", found_idx);
    
    free(a);
    return 0;
}

