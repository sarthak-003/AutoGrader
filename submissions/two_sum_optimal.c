/**
 * Optimal Two-Sum on Sorted Array.
 * Employs two-pointer technique to achieve strict linear O(N) time complexity.
 */
#include <stdio.h>
#include <stdlib.h>

/**
 * Finds two indices whose values sum to the target in sorted array.
 * Returns 1 if pair found, 0 otherwise.
 */
int find_two_sum(const int *array, int array_size, int target_sum, int *out_left, int *out_right) {
    if (!array || array_size < 2) {
        return 0;
    }
    
    int left_ptr = 0;
    int right_ptr = array_size - 1;
    
    while (left_ptr < right_ptr) {
        int current_sum = array[left_ptr] + array[right_ptr];
        if (current_sum == target_sum) {
            *out_left = left_ptr;
            *out_right = right_ptr;
            return 1;
        } else if (current_sum < target_sum) {
            left_ptr++;
        } else {
            right_ptr--;
        }
    }
    return 0;
}

int main(void) {
    int count = 0;
    if (scanf("%d", &count) != 1 || count <= 0) {
        printf("-1\n");
        return 0;
    }
    
    int *numbers = (int *)malloc(count * sizeof(int));
    if (!numbers) return 1;
    
    for (int i = 0; i < count; i++) {
        if (scanf("%d", &numbers[i]) != 1) {
            free(numbers);
            return 1;
        }
    }
    
    int target_value = 0;
    if (scanf("%d", &target_value) != 1) {
        free(numbers);
        return 1;
    }
    
    int index_a = -1;
    int index_b = -1;
    if (find_two_sum(numbers, count, target_value, &index_a, &index_b)) {
        printf("%d %d\n", index_a, index_b);
    } else {
        printf("-1\n");
    }
    
    free(numbers);
    return 0;
}

