//
// Created by David Sere on 28/09/15.
//

#include "CSAOptManager.h"
#include "ModelValidator.h"
#include <uuid/uuid.h>

namespace CSAOpt {


    void CSAOptManager::handleInteractiveCommand(std::string command, std::vector<std::string> args) {
        if (command == "set") {

            logger->info("OK");
        } else if (command == "get") {
            if(args[1] == "all") {
               logger->info(Config::getAll());
            } else if(args.size() > 0 && args[1].size() > 0) {
                std::string val = Config::get(args[1]);
                if(val.length() > 0) {
                    logger->info("{} = {}", args[1], val);
                } else {
                    logger->warn("{} is not defined", args[1]);
                }
            } else {
                logger->warn("No identifier provided");
            }

        } else if (command == "loadModel") {
            if(args.size() < 3) {
               logger->warn("loadOpt expects two parameters: the optimization class and the target class");
            }
            std::string implPath = trim(args[1]);
            std::string key = getFilenameWithoutExtension(trim(implPath));

            loadedModels[key] = {implPath, ""};

            ModelValidator::isValid(implPath, "~/.csaopt/workingdir");
        } else if (command == "exit") {

            logger->info("Invalid command: " + command);
        } else {
            // command not found
            logger->error("Invalid command: " + command);
        }
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
