#include <iostream>
#include <bits/stdc++.h>
using namespace std;    

int main() {
    //Write a program that receives a sentences as a str, and returns the same sentence with the characters reversed.
    string input = "Hello World";

    stack<char> stack;
    for (int i = 0; i < input.length(); i++) {
        if (input[i] == ' ') {
            while (!stack.empty()) {
                cout << stack.top();
                stack.pop();
            }

            cout << " ";
        }

        stack.push(input[i]);
    }

    while (!stack.empty()) {
        cout << stack.top();
        stack.pop();
    }
}