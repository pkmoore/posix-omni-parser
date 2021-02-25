#include <unistd.h>

int main() {
    char buf[256];
    int result = read(5, buf, 10);
    return result;
}