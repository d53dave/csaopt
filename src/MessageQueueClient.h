//
// Created by David Sere on 08/10/15.
//

#pragma once

#include <string>
#include <map>
#include <vector>
#include <Target.h>
#include "OptimizationJob.h"


namespace CSAOpt {

    typedef std::string JobId;

    class MessageQueueClient {

        JobId submit(const OptimizationJob && job);
        void collect(const JobId && id);
        bool didFinish(std::string jobId);

    private:
        std::map<std::string, std::vector<Target>> m;

    };
}


