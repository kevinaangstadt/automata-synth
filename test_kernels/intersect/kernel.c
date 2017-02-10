/*
 * s \in L1 AND s \not\in L2
 * where L1 = (abc)+
 * and L2 = a
 */

int kernel(char* input) {
    int i = 0;
    int l1_accepted = 0;
    if(input[i] == 'a' || input[i] == 'b' || input[i] == 'c') {
        i++;
        while(input[i] == 'a' || input[i] == 'b' || input[i] == 'c') {
            i++;
        }
        l1_accepted = 1;
    } else {
        l1_accepted = 0;
    }
    
    return l1_accepted;
}
