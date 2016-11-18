//
// Created by dotdi on 17.11.16.
//

#pragma once

#include <string>
#include <spdlog/fmt/ostr.h>

class ManagedModel {
public:
    std::string name;
    std::string optClass;
    std::string targetClass;
    std::string modelFilePath;
    std::string compilerCmd;
    std::string errorMessage;
    bool success;

    friend std::ostream &operator<<(std::ostream &os, ManagedModel const &mm) {
        return os << "Model [name=" << mm.name << ", opt=" << mm.optClass << ", target=" << mm.targetClass <<
               ", path=" << mm.modelFilePath << "]";
    }

private:
};
