//
// Created by dotdi on 16.11.16.
//

#pragma once

#include <string>
#include "ModelBuilder.h"
#include "../SysTools.h"
#include "../Config.h"

namespace CSAOpt {
    class ModelValidator {
    public:
        static std::pair<bool, ManagedModel> validate(std::string const &implPath, std::string const &workingDir) {
            // TODO check if absolute path, i.e. begins with / or ~
            auto logger = spdlog::get(Config::loggerName());

            std::string  implPathAbs = relativePathToAbsolute(implPath);



            if(!file_exists(implPathAbs)) {
                ManagedModel model;
                model.modelFilePath = implPathAbs;
                model.success = false;
                logger->error("Cannot read model implementation file at {}", implPathAbs);
                return {false, model};
            }


            std::string createFolderIfNotExist = fmt::format("mkdir -p {}", workingDir);

            int retCode;
            std::string mkWorkingDirOutput = SysTools::runCmdGetCerr(createFolderIfNotExist, retCode);
            if (retCode != 0) {
                ManagedModel model;
                model.modelFilePath = implPathAbs;
                model.success = false;
                model.errorMessage = mkWorkingDirOutput;
                logger->error("Could not prepare validation: {}", mkWorkingDirOutput);
                return {false, model};
            }
            std::string  workingDirAbs = relativePathToAbsolute(workingDir);

            // copy model folder to working directory
            std::string modelPath = relativePathToAbsolute(Config::getModelSrcPath());
            std::string copyDirCmd = fmt::format("cp -r {}/include {}/src/* {} {}", modelPath,
                                                   modelPath, implPathAbs,
                                                   workingDirAbs);
            std::string copyDirOutput = SysTools::runCmdGetCerr(copyDirCmd, retCode);

            if (retCode != 0) {
                ManagedModel model;
                model.modelFilePath = implPathAbs;
                model.success = false;
                model.errorMessage = copyDirOutput;
                logger->error("Could not prepare validation: {}", copyDirOutput);
                return {false, model};
            }

            auto model = ModelBuilder().buildModel(implPathAbs, workingDirAbs);
            model.name = getFilenameWithoutExtension(implPathAbs);
            return {model.success, model};
        }
    };
}

