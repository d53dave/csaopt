#include "ModelOptions.h"

class TestTarget : public Target {
public:
    constexpr DIMENSIONALITY = 2;

    double coords[DIMENSIONALITY];
    double energy;

    __CUDA__ size_t dimensionality() { return DIMENSIONALITY; }
};