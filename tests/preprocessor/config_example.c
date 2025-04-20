// config_example.c


#if defined(_WIN32) || defined(_WIN64)
    #define OS "Windows"
#elif defined(__linux__)
    #define OS "Linux"
#elif defined(__APPLE__)
    #define OS "Mac OS"
#else
    #define OS "Unknown"
#endif

int main() {
    printf("Operating System: %s\n", OS);
    return 0;
}
