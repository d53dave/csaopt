//
// Created by dotdi on 17.11.16.
//

#pragma once

#include "ManagedModel.h"

namespace CSAOpt {
    class ModelBuilder {
    public:
        ManagedModel buildModel(std::string const& modelfile, std::string const& workingDir);

    private:

    };
};
