# 1 "kernel.c"
# 1 "<built-in>"
# 1 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 1 "<command-line>" 2
# 1 "kernel.c"
int aaaab(char* input) {
  const char comp[] = {'a','a','a','a','b'};
  int i = 0;
  while(i < 5) {
    if(comp[i] != input[i]) {
      return 0;
    }
    i++;
  }
  if(input[5] == '\0')
    return 1;
  else
    return 0;
}

int a_star(char* input) {
  int i = 0;
  while(input[i] != '\0') {
    if(input[i] != 'a')
      return 0;
    i++;
  }
  return 1;
}

int b_star(char* input) {
  int i = 0;
  while(input[i] != '\0') {
    if(input[i] != 'b')
      return 0;
    i++;
  }
  return 1;
}

int kernel(char* input) {
  return aaaab(input) || a_star(input) || b_star(input);
}

int main(int argc, char *argv[]) {
if(argc == 2) {
  if(kernel(argv[1]))
  {
    //printf("true\\n");
    ERROR:
    return 0;
  } else {
    //printf("false\\n");
    return 1;
  }
} else {
  //printf("just pass in the string\\n");
  return 10;
}
}
