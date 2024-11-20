#include <iostream>
#include <bits/stdc++.h>
using namespace std;    

template <typename T>
class Kontainer {
    public:
        void add (T element) {
            if (elements.size() < MAX_SIZE) {
                elements.push_back(element);
            } else {
                cout << "CONTAINER IS AT CAPACITY" << endl;
            }
        }

        T findMin() const {
            if (elements.empty()) {
                cout << "ELEMENTS IS EMPTY" << endl;
            }

            T minElement = numeric_limits<T>::max();

            for (auto& element : elements) {
                if (element < minElement) {
                    minElement = element;
                }
            }

            return minElement;
        }

    private:
        const int MAX_SIZE = 100; // Maximum capacity of the container
        vector<T> elements;        // Vector to hold the elements
};

int main() {
    Kontainer<int> intContainer;
    intContainer.add(10);
    intContainer.add(5);
    intContainer.add(15);

    cout << "Minimum in intContainer: " << intContainer.findMin() << endl;
}