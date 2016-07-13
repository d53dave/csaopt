//
// Created by David Sere on 01/10/15.
//

#pragma once

#include <string>
#include <memory>
#include <chrono>
#include "Optimization.h"

namespace CSAOpt {

    class OptimizationJob {
    public:
        std::string jobId;
        std::shared_ptr<Optimization> optimization;
        std::shared_ptr<Target> target;
        std::string getTargetClassFile();
        std::string getOptClassFile();

        std::chrono::milliseconds lastResultTimeStamp;

    private:
        std::string demangle(const char* name);

        template <class T>
        std::string type(const T& t) {
            return demangle(typeid(t).name());
        }
    };
}

