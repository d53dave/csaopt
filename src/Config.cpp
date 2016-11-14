//
// Created by dotdi on 14.11.16.
//

#include "Config.h"

namespace CSAOpt {

    Config::ConfigMap Config::config {
            //initializing defaults
            {"logger.name",            "console"},
            {"logger.path",            "~/.csaopt/"},
            {"logger.filename",        "csaopt.log"},
            {"logger.verbose",         "false"},
            {"ansible.hosts",          "~/.csaopt/hosts"},
            {"optimization.maxcycles", ""},
            {"optimization.classes",   ""},
            {"optimization.targets",   ""},
            {"optimization.type",      ""}
    };
}

