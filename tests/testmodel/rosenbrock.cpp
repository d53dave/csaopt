#include "ModelOptions.h"
#include "Optimization.h"
#include "testtarget.h"


 __CUDA__ Target & Optimization::initialize(Target &state, double *rands) const {
    return generateNext(state, rands);
}

__CUDA__ Target & Optimization::generateNext(Target &state, double *rands) const {
    for (size_t i = 0; i < ((TestTarget &) state).dimensionality(); ++i) {
        ((TestTarget &) state).coords[i] += denormalizeNext(rands[i]);
    }
    return state;
}

__CUDA__ double Optimization::evaluate(Target &state) const {
    double result, t1, t2;
    double *input = ((TestTarget &) state).coords;
    for (size_t i = 0; i < ((TestTarget &) state).dimensionality() - 1; ++i) {
        t1 = (1 - input[i]);
        t2 = (input[i + 1] - input[i] * input[i]);
        result += t2 * t2 + 100 * (t1 * t1);
    }
    ((TestTarget &) state).energy = result;
    return result;
}

__CUDA__ double Optimization::cool(double oldtemp) const {
    return oldtemp * .98;
}

double Optimization::denormalizeNext(double rand) const {
    return rand * 2 - 1; // from 0..1 to -1..1
}