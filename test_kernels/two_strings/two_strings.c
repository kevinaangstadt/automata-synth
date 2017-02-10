int
main
(
 char*
 alice,
 char*
 bob
 )
{
    if(alice[0] == 97 && alice[1] == 97) {
        if(bob[0] == 98 && bob[1] == 88 && bob[2] == 98) {
            ERROR: return 1;
        }
    }
    return 0;
}