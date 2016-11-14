//
// Created by David Sere on 01/10/15.
//

#include "OptimizationJob.h"
#include <typeinfo>

#ifdef __GNUG__
#include <cstdlib>
#include <memory>
#include <cxxabi.h>

std::string CSAOpt::OptimizationJob::demangle(const char* name) {

    int status = 42; // some arbitrary value to eliminate the compiler warning

    std::unique_ptr<char, void(*)(void*)> res {
            abi::__cxa_demangle(name, NULL, NULL, &status),
            std::free
    };

    return (status==0) ? res.get() : name ;
}

#else

// does nothing if not g++
std::string CSAOpt::OptimizationJob::demangle(const char* name) {
    return name;
}

#endif


std::string CSAOpt::OptimizationJob::getTargetClassFile() {
    return type(*target.get());
}

std::string CSAOpt::OptimizationJob::getOptClassFile() {
    return type(*optimization.get());
}
