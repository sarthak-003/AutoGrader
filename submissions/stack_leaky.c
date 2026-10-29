#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Node {
    int v;
    struct Node *n;
};

int main() {
    char cmd[32];
    struct Node *top = NULL;
    
    while (scanf("%s", cmd) == 1) {
        if (strcmp(cmd, "EXIT") == 0) break;
        if (strcmp(cmd, "PUSH") == 0) {
            int val;
            scanf("%d", &val);
            struct Node *new_node = (struct Node*)malloc(sizeof(struct Node));
            new_node->v = val;
            new_node->n = top;
            top = new_node;
        } else if (strcmp(cmd, "POP") == 0) {
            // Bug: does not check if top is NULL, dereferences NULL pointer if empty!
            if (!top) {
                printf("UNDERFLOW\n");
            } else {
                printf("%d\n", top->v);
                // Leaks memory: forgets to free(top)
                top = top->n;
            }
        } else if (strcmp(cmd, "PEEK") == 0) {
            if (!top) printf("EMPTY\n");
            else printf("%d\n", top->v);
        }
    }
    // Entire stack leaked on termination
    return 0;
}

