//
// Created by David Sere on 28/09/15.
//

#include "CSAOptManager.h"
#include <uuid/uuid.h>

namespace CGOpt{
    void CGOptManager::setAnsibleTools(std::shared_ptr<AnsibleTools> _ansibleTools) {
        this->ansibleTools = _ansibleTools;
    }
    void CGOptManager::setAWSTools(std::shared_ptr<AWSTools> _awsTools) {
        this->awsTools = _awsTools;
    }

    std::string CGOptManager::run(OptimizationJob &job) {
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