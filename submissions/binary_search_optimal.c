/**
 * Binary Search Module.
 * Implements logarithmic divide-and-conquer O(log N) search on sorted arrays.
 */
#include <stdio.h>
#include <stdlib.h>

/**
 * Executes binary search with overflow-safe midpoint calculation.
 * Returns 0-based index or -1 if target is not found.
 */
int binary_search(const int *array, int size, int target_value) {
    if (!array || size <= 0) {
        return -1;
    }
    
    int low_bound = 0;
    int high_bound = size - 1;
    
    while (low_bound <= high_bound) {
        // Prevents signed integer overflow: low + (high - low) / 2
        int mid_index = low_bound + (high_bound - low_bound) / 2;
        
        if (array[mid_index] == target_value) {
            return mid_index;
        } else if (array[mid_index] < target_value) {
            low_bound = mid_index + 1;
        } else {
            high_bound = mid_index - 1;
        }
    }
    return -1;
}

int main(void) {
    int element_count = 0;
    if (scanf("%d", &element_count) != 1 || element_count <= 0) {
        printf("-1\n");
        return 0;
    }
    
    int *sorted_numbers = (int *)malloc(element_count * sizeof(int));
    if (!sorted_numbers) return 1;
    
    for (int i = 0; i < element_count; i++) {
        if (scanf("%d", &sorted_numbers[i]) != 1) {
            free(sorted_numbers);
            return 1;
        }
    }
    
    int search_target = 0;
    if (scanf("%d", &search_target) != 1) {
        free(sorted_numbers);
        return 1;
    }
    
    int result_index = binary_search(sorted_numbers, element_count, search_target);
    printf("%d\n", result_index);
    
    free(sorted_numbers);
    return 0;
}

