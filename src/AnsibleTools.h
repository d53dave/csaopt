//
// Created by David Sere on 28/09/15.
//

#pragma once

#include "AWS/AWSTools.h"

namespace CSAOpt{
    class AnsibleTools {
    public:
        void writeHostsFile(std::vector<CSAOptInstance> instances);
        void setHostsFilePath(std::string _hostsFilePath){ this->hostsFilePath = _hostsFilePath;};
        ~AnsibleTools() {
            if(hostsFilePath.size() > 0){
                unlink(hostsFilePath.c_str());
            }
        }
    private:
        std::string hostsFilePath;

    };
}

