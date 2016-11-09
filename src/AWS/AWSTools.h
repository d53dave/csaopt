//
// Created by David Sere on 28/09/15.
//

#include <vector>
#include <iostream>
#include <stdlib.h>
#include <pwd.h>
#include <unistd.h>
#include <aws/ec2/EC2Client.h>
#include <aws/core/Aws.h>
#include "../SysTools.h"
#include "spdlog/spdlog.h"
#include "../config.hpp"
#include "CSAOptInstance.h"

#pragma once
namespace CSAOpt {
    typedef std::map<InstanceId, CSAOptInstance> WorkingSet;


    class AWSTools : public SysTools {
    public:
        enum AWSRegion {
            USEAST1, USWEST2, USWEST1, EUWEST1, EUCENTRAL1, APSOUTHEAST1, APSOUTHEAST2, APNORTHEAST1, SAEAST1
        };


        AWSTools(const std::string &_awsAccessKey,
                 const std::string &_awsSecretAccessKey,
                 const AWSTools::AWSRegion _region = AWSRegion::EUCENTRAL1,
                 size_t _instanceCount = 1);

        void runSetup();

        WorkingSet getInstances() const;

        void setTerminateOnExit(bool _terminateOnExit) { this->terminateOnExit = _terminateOnExit; };

        void setMessageQueueType(std::string serverType) { this->messageQueueAWSServerType = serverType; };


        ~AWSTools() {
            bool printNotice = false;
            for (auto &&kvp : this->workingSet) {
                if (kvp.second.state == CSAOptInstance::InstanceState::running) {
                    _logger->alert("AWSTools is shutting down but instance with id {} is still running.", kvp.first);
                    printNotice = true;
                }
            }

            if (printNotice) {
                _logger->alert("ATTENTION: It appears that not all instances could be stopped/terminated.\n"
                                       "Please verify the state of the instances in your AWS console and manually"
                                       "turn off instances that were left behind. Sorry :/");
            }
        };

    private:


        // STRINGS
        const std::string regionEnumStrings[10] = {"us-east-1", "us-west-2", "us-west-1", "eu-west-1", "eu-central-1",
                                                   "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "sa-east-1"};
        const std::string UBUNTU14_4_HVM_AMI{"ami-47a23a30"};
        const std::string CUDA_AMI{"ami-f88281e5"};
        const std::string G2_2X_LARGE{"g2.2xlarge"};
        const std::string G2_8X_LARGE{"g2.8xlarge"};
        const std::string T2_MICRO{"t2.micro"};
        const std::string T2_SMALL{"t2.small"};
        const std::string M3_MEDIUM{"m3.medium"};
        std::string secGroupName;   // in constructor
        std::string home;           // in constructor
        std::string keyName;        // in constructor
        std::string keyPath;        // in constructor
        std::string myIp;           // in constructor
        std::string messageQueueAWSServerType;

        std::shared_ptr<spdlog::logger> _logger;

        // PRIVATE DATA
        std::string awsAccessKey, awsSecretAccessKey;
        AWSRegion region;
        size_t instanceCount;
        bool terminateOnExit = false;
        bool useSeparateMachineAsMsgQueue = false;
        WorkingSet workingSet;
        CSAOptInstance messageQueue;
        std::string trackingTag;

        // Methods
        void setupLogger();

        std::string createSecGroup(std::string name, Aws::EC2::EC2Client &client);


        bool keyPresentLocally(std::string path);


        void terminateInstances(std::map<Aws::String, std::string> instanceIps, Aws::EC2::EC2Client &client);

        CSAOptInstance &getMessageQueue();

        std::string getLocalIp() const;

        std::string getKeyMaterial(std::string name, Aws::EC2::EC2Client &client);

        WorkingSet startInstances(int instanceCount, Aws::EC2::Model::InstanceType instanceType,
                                            Aws::EC2::EC2Client &client);

        std::map<InstanceId, std::string> getInstanceAddresses(const WorkingSet &instances,
                                                               Aws::EC2::EC2Client &client) const;

        void shutdownInstances(std::map<Aws::String, std::string> instanceIps, Aws::EC2::EC2Client &client);

        void shutdown(Aws::EC2::EC2Client &client);

        void waitUntilRunning(const std::vector<Aws::String> instanceIds, Aws::EC2::EC2Client &client) const;
    };

}



