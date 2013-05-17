#include <string>
#include <iostream>
#include <thread>
#include <mutex>

using namespace std;

void startStream(string stream);
void task1(string stream);

std::mutex m;
int counter = 0;

void task1(string stream)
{
    startStream(stream);
}

void startStream(string stream)
{
    std::unique_lock<std::mutex> lock(m);
    counter++;
    cout << "Starting Stream: " << stream << "\n";
}

int main(int argc, char **argv)
{
    int count = 1;
    if (argc == 2) count = atoi(argv[1]);
    int i;
    thread threads[count];
    for (i=0; i < count; i++) {
        threads[i] = thread(task1, "stream");
    }
    for (i=0; i < count; i++) {
        threads[i].join();
    }
    cout << "counter: " << counter;
}
