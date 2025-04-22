    char name[50];
    int age;
    float height;
    struct __attribute__((aligned(8))) Address {
        char street[100];
        char city[50];
        char state[20];
        int zip_code;
    } address;
} __attribute__((aligned(16)));


union __declspec(dllexport) Data {
    int intValue;
    float floatValue;
    char strValue[20];
    union {
        long longValue;
        double doubleValue;
    } nestedData __attribute__((aligned(8)));
} __attribute__((packed));