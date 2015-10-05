//
// Created by David Sere on 01/10/15.
//

#pragma once

#include "Target.h"

class UserDefinedTarget: public CGOpt::Target {
public:
    int getAnswer();

    virtual std::string getIdentifier() const;
};


