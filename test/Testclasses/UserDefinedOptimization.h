//
// Created by David Sere on 01/10/15.
//

#pragma once

#include "Optimization.h"

class UserDefinedOptimization : public CGOpt::Optimization{
    __CUDA__ virtual CGOpt::Target &initialize(CGOpt::Target &state, double *rands) const;

    __CUDA__ virtual CGOpt::Target &generateNext(CGOpt::Target &state, double *rands) const;

    __CUDA__ virtual OPT_TYPE_RETURN evaluate(CGOpt::Target &state) const;

    __CUDA__ virtual OPT_TYPE_RETURN cool(double oldtemp) const;
};


