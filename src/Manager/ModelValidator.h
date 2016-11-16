//
// Created by dotdi on 16.11.16.
//

#pragma once

#include <string>
#include "../SysTools.h"
#include "../Config.h"

namespace CSAOpt {
    class ModelValidator {
    public:
        static bool isValid(std::string const &impl, std::string const &workingDirectory) {
            auto logger = spdlog::get(Config::loggerName());

            int retCode;
            std::string modelPath = Config::getModelSrcPath();
            // copy model folder to working directory
            std::string copyDirCmd = string_format("cp -r $%s/include $%s/src/* %s %s", modelPath.c_str(),
                                                   modelPath.c_str(), impl.c_str(),
                                                   workingDirectory.c_str());
            std::string copyDirOutput = SysTools::runCmdGetCerr(copyDirCmd, retCode);

            if (retCode != 0) {
                logger->error("Could not prepare validation: {}", copyDirOutput);
            }

            // build gcc command
            std::string compilerCmd = string_format("g++ -std=c++11 %s -Iinclude -c", getFilenameFromPath(impl).c_str());

            // run and capture output
            std::string compilerOutput = SysTools::runCmdGetCerr(compilerCmd, retCode);

            if (retCode != 0) {
                logger->error("Could not prepare validation: {}", compilerOutput);
            }

            return true;
        }
    };
}

