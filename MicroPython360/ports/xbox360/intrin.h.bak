#pragma once

static __inline unsigned char _BitScanReverse(unsigned long *Index, unsigned long Mask) {
    if (Mask == 0) {
        *Index = 0;
        return 0;
    }
    *Index = 0;
    while ((Mask >>= 1) != 0) {
        ++(*Index);
    }
    return 1;
}

static __inline unsigned char _BitScanForward(unsigned long *Index, unsigned long Mask) {
    if (Mask == 0) {
        *Index = 0;
        return 0;
    }
    *Index = 0;
    while ((Mask & 1) == 0) {
        Mask >>= 1;
        ++(*Index);
    }
    return 1;
}
