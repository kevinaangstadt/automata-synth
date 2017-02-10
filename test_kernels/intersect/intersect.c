/*
 * s \in L1 AND s \not\in L2
 * where L1 = (abc)+
 * and L2 = a
 */

int main(char* input) {
    int i = 0;
    int l1_accepted = 0;
    int l2_accepted = 0;
    if(input[i] == 'a' || input[i] == 'b' || input[i] == 'c') {
        i++;
        while(input[i] == 'a' || input[i] == 'b' || input[i] == 'c') {
            i++;
        }
        l1_accepted = 1;
    } else {
        l1_accepted = 0;
    }
    
    i = 0;
    if (input[i] == 'a' || input[i] == 'b') {
        l2_accepted = 1;
    } else {
        l2_accepted = 0;
    }
    
    if(l1_accepted && !l2_accepted) {
        ERROR: return 1;
    } else {
        return 0;
    }
}