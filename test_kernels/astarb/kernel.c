int kernel(char* input) {
  int i = 0;
  while( input[i] == 'a' ) {
    i++;
  }
  if( input[i] == 'b' ) {
    return 1;
  } else {
    return 0;
  }
}
