/**
 * Palindrome Verification Module.
 * Modular, memory-safe, and linear time O(N) palindrome detector.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/**
 * Checks if a string is a palindrome, ignoring non-alphanumeric characters.
 * Runs in strict linear time O(N).
 */
int is_palindrome(const char *input_text) {
    if (!input_text) return 0;
    
    int left_index = 0;
    int right_index = (int)strlen(input_text) - 1;
    
    while (left_index < right_index) {
        while (left_index < right_index && !isalnum((unsigned char)input_text[left_index])) {
            left_index++;
        }
        while (left_index < right_index && !isalnum((unsigned char)input_text[right_index])) {
            right_index--;
        }
        
        if (tolower((unsigned char)input_text[left_index]) != tolower((unsigned char)input_text[right_index])) {
            return 0;
        }
        left_index++;
        right_index--;
    }
    return 1;
}

int main(void) {
    char *input_buffer = (char *)malloc(1024 * sizeof(char));
    if (!input_buffer) return 1;
    
    if (fgets(input_buffer, 1024, stdin)) {
        size_t buffer_len = strlen(input_buffer);
        if (buffer_len > 0 && input_buffer[buffer_len - 1] == '\n') {
            input_buffer[buffer_len - 1] = '\0';
        }
        
        if (is_palindrome(input_buffer)) {
            printf("YES\n");
        } else {
            printf("NO\n");
        }
    }
    
    // Explicit clean deallocation to ensure 0 memory leaks
    free(input_buffer);
    return 0;
}

