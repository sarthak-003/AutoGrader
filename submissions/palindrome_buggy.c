#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    char s[100];
    if (!fgets(s, sizeof(s), stdin)) return 0;
    
    // Intentionally leak memory
    char *copy = (char*)malloc(100);
    strcpy(copy, s);
    
    int len = strlen(s);
    if (len > 0 && s[len - 1] == '\n') {
        s[len - 1] = '\0';
        len--;
    }
    
    // Does not ignore spaces or handle phrases properly
    int p = 1;
    for (int i = 0; i < len / 2; i++) {
        if (s[i] != s[len - 1 - i]) {
            p = 0;
            break;
        }
    }
    
    if (p) printf("YES\n");
    else printf("NO\n");
    
    // Notice: free(copy) is omitted to cause a real memory leak
    return 0;
}

