//
// Created by dotdi on 17.11.16.
//

#include <spdlog/spdlog.h>
#include <regex>
#include "ModelBuilder.h"
#include "../Config.h"
#include "../SysTools.h"

namespace CSAOpt {

    ManagedModel ModelBuilder::buildModel(std::string const &modelfile, std::string const &workingDir) {
        auto logger = spdlog::get(Config::loggerName());
        ManagedModel model;
        model.success = true;
        model.modelFilePath = modelfile;

        std::ifstream file(modelfile);
        std::string reBase = "\\s*class\\s*(\\S+)\\s*:\\s*public\\s*{}\\s*";
        std::regex optRe(fmt::format(reBase, "Optimization"));
        std::regex targetRe(fmt::format(reBase, "Target"));
        std::smatch sMatchOpt;
        std::smatch sMatchTarget;

        size_t linecount = 0;
        std::string line;
        while (std::getline(file, line)) {
            ++linecount;
            if (line.empty()) {
                continue;
            }

//            if(linecount == 7 || linecount == 16) {
//                file.good();
//            }

            if (std::regex_search(line, sMatchOpt, optRe) && sMatchOpt.size() > 1) {
                model.optClass = sMatchOpt.str(1);

                if (!model.targetClass.empty()) {
                    break;
                }
            } else if (std::regex_search(line, sMatchTarget, targetRe) && sMatchTarget.size() > 1) {
                model.targetClass = sMatchTarget.str(1);

                if (!model.optClass.empty()) {
                    break;
                }
            }
        }

        if (model.optClass.empty()) {
            logger->error("Could not find Optimization implementation in {}", modelfile);
            model.success = false;
        }
        if (model.targetClass.empty()) {
            model.success = false;
            logger->error("Could not find Target implementation in {}", modelfile);
        }


        if (model.success) { // i.e. if model still good
            int retCode = 0;

            // build gcc command
            std::string compilerCmd = fmt::format("g++ -std=c++11 {0}/{1} -I{0}/include -iquote{0} -c -o {0}/{2}.o",
                                                  workingDir, getFilenameFromPath(modelfile),
                                                   getFilenameWithoutExtension(modelfile));
            model.compilerCmd = compilerCmd;

            // run and capture cerr output
            std::string compilerOutput = SysTools::runCmdGetCerr(compilerCmd, retCode);

            if (retCode != 0) {
                logger->error("Could not prepare validation: {}", compilerOutput);
                model.errorMessage = compilerOutput;
                model.success = false;
            } else {
                model.success = true;
            }
        }

        return model;
    }
}

