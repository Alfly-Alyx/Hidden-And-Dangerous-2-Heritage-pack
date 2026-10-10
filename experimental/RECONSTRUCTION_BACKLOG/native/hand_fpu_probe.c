/* Original standalone console probe. No game, DLL loader or process access.
 * Verifies all 108 bytes across the same x87 save/restore sequence as the
 * adapter, including instruction/data exception-address fields.
 */
#include <stdio.h>
#include <string.h>
void Hd2FpuRoundtrip(unsigned char *,unsigned char *);
int main(void) {
    unsigned char before[108]={0},after[108]={0};unsigned i;
    Hd2FpuRoundtrip(before,after);
    for(i=0;i<108;i++) if(before[i]!=after[i]) {
        printf("x87 state mismatch at byte %u: %u != %u\n",i,before[i],after[i]);return 1;
    }
    puts("PASS: all 108 x87 state bytes preserved, including exception addresses");
    return 0;
}
