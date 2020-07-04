'use strict';


function clamp(x, lo, hi) {
    return Math.max(lo, Math.min(hi, x));
}


export { clamp };