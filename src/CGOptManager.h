//
// Created by David Sere on 28/09/15.
//
#pragma once

#include <typeinfo>
#include <vector>
#include <string>
#include "OptimizationJob.h"
#include "../model/src/Target.h"
#include "../model/src/Optimization.h"

namespace CGOpt {

    class CGOptManager {
    public:
        static CGOptManager& getInstance()
        {
            static CGOptManager instance; // Guaranteed to be destroyed.
            // Instantiated on first use.
            return instance;
        }

        std::string run(OptimizationJob &job);
        void abort();
        std::vector<Target> getResults(std::string jobId);
    private:
        CGOptManager() {};
        CGOptManager(CGOptManager const&)   = delete;
        void operator=(CGOptManager const&) = delete;
    };
}


