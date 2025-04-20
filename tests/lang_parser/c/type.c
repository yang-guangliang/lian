#define VECTOR(type) \
    struct { \
        type *data; \
        size_t size; \
        size_t capacity; \
    }

VECTOR(int) int_vector;  
VECTOR(float) float_vector;