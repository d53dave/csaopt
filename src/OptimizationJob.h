//
// Created by David Sere on 01/10/15.
//

#pragma once

#include <string>
#include <memory>
#include "Optimization.h"

namespace CGOpt {



    class OptimizationJob {
    public:
        std::string jobId;
        std::shared_ptr<Optimization> optimization;
        std::shared_ptr<Target> target;
        std::string getTargetClassFile();
        std::string getOptClassFile();

    private:
        std::string demangle(const char* name);

        template <class T>
        std::string type(const T& t) {
            return demangle(typeid(t).name());
        }
    };
}

