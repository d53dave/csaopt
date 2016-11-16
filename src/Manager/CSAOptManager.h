//
// Created by David Sere on 28/09/15.
//
#pragma once

#include <typeinfo>
#include <vector>
#include <string>
#include "../OptimizationJob.h"
#include "../AWS/AWSTools.h"
#include "../AnsibleTools.h"
#include <Target.h>
#include <map>

namespace CSAOpt {

    class CSAOptManager {
    public:
        typedef struct {
            std::string implPath;
            std::string targetPath;
        } OptModel;

        static CSAOptManager& getInstance()
        {
            static CSAOptManager instance; // Guaranteed to be destroyed.
            // Instantiated on first usee.
            return instance;
        }

        void handleInteractiveCommand(std::string command, std::vector<std::string> args);
        void handleBatchStart();


        std::vector<Target> getResults(std::string jobId);
        std::vector<Target> getResultsBlocking(std::string jobId);

        bool newResultsAvailable();
        bool newResultsAvailable(std::string jobId);
    private:
        //singleton stuff
        CSAOptManager() {
            this->logger = spdlog::get(Config::loggerName());
        };
        CSAOptManager(CSAOptManager const&)  = delete;
        void operator=(CSAOptManager const&) = delete;

        std::shared_ptr<spdlog::logger> logger;

        std::string run(OptimizationJob &job);
        void setAWSTools(std::shared_ptr<AWSTools> _awsTools);
        void setAnsibleTools(std::shared_ptr<AnsibleTools> _ansibleTools);
        void abort();

        std::map<std::string, OptimizationJob> jobCache;
        std::shared_ptr<AWSTools> awsTools;
        std::shared_ptr<AnsibleTools> ansibleTools;

        std::map<std::string, OptModel> loadedModels;

        ~CSAOptManager() {

        }
    };
}


