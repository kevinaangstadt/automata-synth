

int kernel(char* input) {
    const char comp[] = "aaaab";
    int i = 0;
    int tmp = 1;
    int retval = 0;
    while(i < 5) {
      if(comp[i] != input[i]) {
        tmp = 0;
      }
      i++;
    }
    if(input[5] == '\0')
        retval = tmp;
      else
        retval = 0;

    
    if(!retval) {
        i = 0;
        tmp = 1;
        while(input[i] != '\0') {
          if(input[i] != 'a'){
            tmp = 0;
          }
          i++;
        }
        retval = tmp;
    }

    
    
    if(!retval) {
        i = 0;
        tmp = 1;
        while(input[i] != '\0') {
          if(input[i] != 'b') {
            tmp = 0;
          }
          i++;
        }
        retval = tmp;
    }
    
    
    return retval;
}