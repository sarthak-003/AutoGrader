/**
 * Safe Addition Module.
 * Computes sum of integers safely and provides modular architecture.
 */
#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
  #define FMT_LLD "%I64d"
#else
  #define FMT_LLD "%lld"
#endif

/* Helper function performing safe addition */
long long safe_add(long long lhs, long long rhs) {
    return lhs + rhs;
}

int main(void) {
    long long operand_a, operand_b;
    if (scanf(FMT_LLD " " FMT_LLD, &operand_a, &operand_b) != 2) {
        return 1;
    }

    long long sum_result = safe_add(operand_a, operand_b);
    printf(FMT_LLD "\n", sum_result);
    return 0;
}
