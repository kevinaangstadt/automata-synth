int main() {
  int i=0;
  int x=0;
  char foo[] = "aab";
  for(i=0; i<6; i++) {
    x = x+i;
  }
  if(foo[0] == foo[1]) {
    ERROR: return 1;
  }
  return 0;
}
