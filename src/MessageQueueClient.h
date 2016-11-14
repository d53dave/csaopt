//
// Created by David Sere on 08/10/15.
//

#pragma once

#include <string>
#include <map>
#include <vector>
#include <Target.h>


namespace CSAOpt {
    class MessageQueueClient {

        bool didFinish(std::string jobId);

    private:
        std::map<std::string, std::vector<Target>> m;

    };
}


