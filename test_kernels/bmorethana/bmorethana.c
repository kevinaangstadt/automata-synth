int main(char* input) {
    int i = 0;
    int j = 0;
    int temp = 0;
    
    while (input[i] == 'a') {
        i++;
    }
    
    temp = i;
    
    while (input[temp] == 'b') {
        j++;
        temp++;
    }
    
    if (j > i && i > 1) {
        ERROR: return 1;
    } else {
        return 0;
    }
}