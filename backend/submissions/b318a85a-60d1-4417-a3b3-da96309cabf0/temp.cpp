#include <iostream>
#include <vector>

using namespace std;

int main() {
    // Malicious Attack: Attempt to consume 5 Gigabytes of RAM instantly
    vector<long long> memory_bomb;
    while(true) {
        memory_bomb.push_back(1000000000);
    }
    return 0;
}