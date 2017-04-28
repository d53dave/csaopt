//
// Created by David Sere on 01/10/15.
//

#pragma once

#include "Optimization.h"

class UserDefinedOptimization : public CSAOpt::Optimization{
    __CUDA__ virtual CSAOpt::Target &initialize(CSAOpt::Target &state, double *rands) const;

    __CUDA__ virtual CSAOpt::Target &generateNext(CSAOpt::Target &state, double *rands) const;

    __CUDA__ virtual OPT_TYPE_RETURN evaluate(CSAOpt::Target &state) const;

    __CUDA__ virtual OPT_TYPE_RETURN cool(double oldtemp) const;
};


