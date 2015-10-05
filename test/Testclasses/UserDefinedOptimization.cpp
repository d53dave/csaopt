//
// Created by David Sere on 01/10/15.
//

#include "UserDefinedOptimization.h"
#include "UserDefinedTarget.h"

OPT_TYPE_RETURN UserDefinedOptimization::cool(double oldTemp) const { return oldTemp-1; }
OPT_TYPE_RETURN UserDefinedOptimization::evaluate(CGOpt::Target &state) const {
    return static_cast<UserDefinedTarget&>(state).getAnswer();
}
CGOpt::Target & UserDefinedOptimization::generateNext(CGOpt::Target &state, double *const rands) const { return state; }
CGOpt::Target & UserDefinedOptimization::initialize(CGOpt::Target &state, double *const rands) const {
    return generateNext(state, 0);
}

