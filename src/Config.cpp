//
// Created by dotdi on 14.11.16.
//

#include "Config.h"

namespace CSAOpt {
    const std::string basePath = "~./.csaopt/";

    Config::ConfigMap Config::config{
            //initializing defaults
            {"logger.name",            "console"},
            {"logger.path",            basePath},
            {"logger.filename",        "csaopt.log"},
            {"logger.verbose",         "false"},
            {"interactive.histpath",   basePath + ".hist"},
            {"ansible.hosts",          basePath + "hosts"},
            {"optimization.maxcycles", ""},
            {"optimization.classes",   ""},
            {"optimization.targets",   ""},
            {"optimization.type",      ""},
            {"optimization.modelSrcPath", CSAOPT_MODEL_PATH} //passed in as a -D by CMake
    };
}

