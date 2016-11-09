//
// Created by David Sere on 28/09/15.
//
#pragma once

#include <typeinfo>
#include <vector>
#include <string>
#include "OptimizationJob.h"
#include <model/Target.h>
#include <model/Optimization.h>
#include "AWS/AWSTools.h"
#include "AnsibleTools.h"
#include <map>

namespace CSAOpt {

    class CSAOptManager {
    public:
        static CSAOptManager& getInstance()
        {
            static CSAOptManager instance; // Guaranteed to be destroyed.
            // Instantiated on first use.
            return instance;
        }

        std::string run(OptimizationJob &job);
        void setAWSTools(std::shared_ptr<AWSTools> _awsTools);
        void setAnsibleTools(std::shared_ptr<AnsibleTools> _ansibleTools);
        void abort();
        std::vector<Target> getResults(std::string jobId);
        std::vector<Target> getResultsBlocking(std::string jobId);

        bool newResultsAvailable();
        bool newResultsAvailable(std::string jobId);
    private:
        //singleton stuff
        CSAOptManager() {};
        CSAOptManager(CSAOptManager const&)   = delete;
        void operator=(CSAOptManager const&) = delete;

        std::map<std::string, OptimizationJob> jobCache;
        std::shared_ptr<AWSTools> awsTools;
        std::shared_ptr<AnsibleTools> ansibleTools;

        ~CGOptManager() {
            if(this->awsTools != nullptr){
               delete( this->awsTools );
            }
        }
    };
}


