
#include <pcre.h>
#include <string.h>
#include <stdio.h>

#define OVECCOUNT 30
int kernel(char* input) {
    if(strcmp(input, "aaaab") == 0)
        return 1;

    pcre *regex = NULL;
    const char *err_msg;
    int erroroffset;
    int err;
    int ovector[OVECCOUNT];

    regex = pcre_compile("^(a*|b*)$", 0, &err_msg, &err, NULL);

    if (regex == NULL)
    {
         //printf("PCRE compilation failed at offset %d: %s\n", erroroffset, err_msg);
         return 0;
    }
    err = pcre_exec(regex, NULL, input, strlen(input), 0, 0, ovector, OVECCOUNT);

    if (err < 0) {
        switch(err) {
            case PCRE_ERROR_NOMATCH: 
                 pcre_free(regex);
                 //printf("no match found\n");
                 return 0;
            default: //printf("Matching error %d\n", err); 
                 pcre_free(regex); return 0;
        }
    } else {
        pcre_free(regex);
        return 1;
    }
}


int main(int argc, char *argv[]) {
  if(argc == 2)
  {
    if(kernel(argv[1]))
    {
      //printf("true\n");
      ERROR: return 0;
    } else {
      //printf("false\n");
      return 1;
    }
  } else {
    //printf("just pass in the string\n");
    return 10;
  }
}
