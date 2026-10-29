/**
 * Robust Dynamic Stack Module.
 * Fully modular, memory-leak free dynamic stack with underflow protection.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct StackNode {
    int value;
    struct StackNode *next;
} StackNode;

typedef struct {
    StackNode *top;
    int size;
} Stack;

void init_stack(Stack *stack) {
    if (stack) {
        stack->top = NULL;
        stack->size = 0;
    }
}

int push(Stack *stack, int val) {
    if (!stack) return 0;
    StackNode *node = (StackNode *)malloc(sizeof(StackNode));
    if (!node) return 0;
    node->value = val;
    node->next = stack->top;
    stack->top = node;
    stack->size++;
    return 1;
}

int pop(Stack *stack, int *out_val) {
    if (!stack || !stack->top) {
        return 0; // Underflow
    }
    StackNode *temp = stack->top;
    if (out_val) {
        *out_val = temp->value;
    }
    stack->top = temp->next;
    free(temp); // Free popped node to prevent leaks
    stack->size--;
    return 1;
}

int peek(const Stack *stack, int *out_val) {
    if (!stack || !stack->top) {
        return 0; // Empty
    }
    if (out_val) {
        *out_val = stack->top->value;
    }
    return 1;
}

void free_stack(Stack *stack) {
    if (!stack) return;
    int dummy = 0;
    while (pop(stack, &dummy)) {
        // Repeatedly free all nodes
    }
}

int main(void) {
    Stack my_stack;
    init_stack(&my_stack);
    
    char command[32];
    while (scanf("%31s", command) == 1) {
        if (strcmp(command, "EXIT") == 0) {
            break;
        } else if (strcmp(command, "PUSH") == 0) {
            int val = 0;
            if (scanf("%d", &val) == 1) {
                push(&my_stack, val);
            }
        } else if (strcmp(command, "POP") == 0) {
            int popped_val = 0;
            if (pop(&my_stack, &popped_val)) {
                printf("%d\n", popped_val);
            } else {
                printf("UNDERFLOW\n");
            }
        } else if (strcmp(command, "PEEK") == 0) {
            int peek_val = 0;
            if (peek(&my_stack, &peek_val)) {
                printf("%d\n", peek_val);
            } else {
                printf("EMPTY\n");
            }
        }
    }
    
    // Explicit cleanup of any remaining nodes
    free_stack(&my_stack);
    return 0;
}

