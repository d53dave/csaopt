//
// Created by David Sere on 28/09/15.
//

#include "CSAOptManager.h"
#include "ModelValidator.h"
#include <uuid/uuid.h>
#include <ctime>

namespace CSAOpt {

    bool CSAOptManager::interactiveHandleLoad(std::vector<std::string> args) {
        bool doContinue = true;
        if (args.size() < 3) {
            logger->error("The load command expects at least 2 arguments.");
            return doContinue;
        }

        std::string load = args[1];
        if (load == "model") {
            std::string implPath = args[2];
            std::string key = getFilenameWithoutExtension(implPath);


            std::string timestamp = std::to_string(std::time(nullptr));

            auto successAndModel = ModelValidator::validate(implPath,
                                                            ("~/.csaopt/workingdir" + timestamp));
            if (successAndModel.first) {
                logger->info("{} loaded successfully", successAndModel.second);
                loadedModels[key] = successAndModel.second;
            } else {
                logger->error("Model [file={}] could not be loaded", successAndModel.second.modelFilePath);
            }

        } else if (load == "config") {

        } else {
            logger->error("Unrecognized load command: {}", load);
        }
        return doContinue;
    }

    bool CSAOptManager::interactiveHandleGet(std::vector<std::string> args) {
        bool doContinue = true;
        if (args.size() < 3) {
            logger->error("The get command expects at least 2 arguments.");
            return doContinue;
        }

        if(args[1] == "config") {
            if (args[2] == "all") {
                logger->info(Config::getAll());
            } else if (args.size() > 2 && args[2].size() > 0) {
                std::string val = Config::get(args[2]);
                if (val.length() > 0) {
                    logger->info("{} = {}", args[2], val);
                } else {
                    logger->warn("{} is not defined", args[2]);
                }
            } else {
                logger->warn("No identifier provided");
            }
        } else if(args[1] == "model") {
            if (args[2] == "all") {
                if(this->loadedModels.empty()) {
                    logger->warn("No loaded models");
                    return doContinue;
                }

                std::stringstream ss;
                for(auto &&kvp : this->loadedModels) {
                    ss << kvp.second << std::endl;
                }
                logger->info(ss.str());
            } else if (args.size() > 2 && args[2].size() > 0) {
                std::string modelname = args[2];
                if (this->loadedModels.count(modelname) > 0) {
                    logger->info("{}", this->loadedModels[modelname]);
                } else {
                    logger->warn("{} is not loaded.", args[2]);
                }
            } else {
                logger->warn("No identifier provided.");
            }
        } else {
            logger->error("Unrecognized option {} for command {}", args[1], args[2]);
        }
        return doContinue;
    }



    bool CSAOptManager::handleInteractiveCommand(std::string command, std::vector<std::string> args) {
        bool doContinue = true;
        if (command == "set") {

            logger->info("OK");

        } else if (command == "help") {

        } else if (command == "get") {
            return interactiveHandleGet(args);
        } else if (command == "load") {
            return interactiveHandleLoad(args);
        } else if (command == "exit") {
            doContinue = false;
        } else {
            // command not found
            logger->error("Invalid command: " + command);
        }
        return doContinue;
    }


    void CSAOptManager::setAnsibleTools(std::shared_ptr<AnsibleTools> _ansibleTools) {
        this->ansibleTools = _ansibleTools;
    }

    void CSAOptManager::setAWSTools(std::shared_ptr<AWSTools> _awsTools) {
        this->awsTools = _awsTools;
    }

    std::string CSAOptManager::run(OptimizationJob &job) {
        if (this->awsTools == nullptr) {
            const char *accessKey = std::getenv("AWS_Access_Key_ID");
            const char *secretKey = std::getenv("AWS_Secret_Access_Key");

            assert(accessKey && secretKey);

            this->awsTools = std::make_shared<AWSTools>(accessKey, secretKey);
        }
        if (this->ansibleTools == nullptr) {
            this->ansibleTools = std::make_shared<AnsibleTools>();
        }

        char uuidBuf[36];
        uuid_t uuidGenerated;
        uuid_generate_random(uuidGenerated);
        uuid_unparse(uuidGenerated, uuidBuf);

        std::string jobId = std::string{uuidBuf};
        job.jobId = jobId;

        //put job and results vector into cache
        jobCache[jobId] = job;

        //actually run the job;

        //return job id
        return jobId;
    }
}
