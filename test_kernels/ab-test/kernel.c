int aaaab(char* input) {
  const char comp[] = "aaaab";
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
  return input[0] != '\0' && ( aaaab(input) || a_star(input) || b_star(input) );
}
