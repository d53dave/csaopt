//
// Created by David Sere on 28/09/15.
//

#include "AnsibleTools.h"
#include "config.hpp"
#include <fstream>

void CSAOpt::AnsibleTools::writeHostsFile(std::vector<AWSTools::AWSInstance> instances) {
    assert(hostsFilePath.size() > 0);

    std::ofstream outputFile( hostsFilePath );
    outputFile << "[worker]\n";

    AWSTools::AWSInstance* messageQueue = nullptr;
    for(auto &instance: instances){
        if(instance.isWorker){
            outputFile << instance.publicIp << "\n";
        }
        if(instance.isMessageQueue){
            if(messageQueue != nullptr){
                throw std::logic_error("Only one message queue instance is allowed");
            }
            messageQueue = &instance;
        }
    }

    outputFile << "[msgqueue]\n";
    outputFile << messageQueue->publicIp << "\n";

    outputFile.flush();
    outputFile.close();
}
