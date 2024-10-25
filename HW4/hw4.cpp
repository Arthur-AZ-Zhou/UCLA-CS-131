#include <iostream>
#include <string>
#include <stack>
#include <bits/stdc++.h>
using namespace std;    
        
int longestRun(vector<bool> boolVec) {
    int longestAnswer = 0;
    int answer = 0;

    for (int i = 0; i < boolVec.size(); i++) {
        if (boolVec[i]) {
            answer++;
        } else {
            longestAnswer = max(longestAnswer, answer);
            answer = 0;
        }
    }

    return max(longestAnswer, answer);
}

class Tree {
    public:
        unsigned value;
        vector<Tree *> children;
        Tree(unsigned value, vector<Tree *> children) {
        this->value = value;
        this->children = children;
    }
};


unsigned maxTreeValue(Tree* root) {
    if (root == nullptr) {
        return 0;
    }

    unsigned maxValue = root->value;
    stack<Tree*> nodes;
    nodes.push(root);

    while (!nodes.empty()) {
        Tree* current = nodes.top();
        nodes.pop();

        // Update maxValue if the current node's value is greater
        maxValue = max(maxValue, current->value);

        // Add all children to the stack
        for (Tree* child : current->children) {
            if (child != nullptr) {
                nodes.push(child);
            }
        }
    }

    return maxValue;
}

int main() {
    vector<bool> boolVec = {true, true, false, true, true, true, false};
    cout << longestRun(boolVec) << endl;
}