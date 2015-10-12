//
// Created by David Sere on 28/09/15.
//
#define PICOJSON_USE_INT64

#include <vector>
#include <iostream>
#include <stdlib.h>
#include <pwd.h>
#include <unistd.h>
#include "picojson/picojson.h"
#include "SysTools.h"
#include "spdlog/spdlog.h"
#include "config.hpp"

#pragma once
namespace CGOpt {
    class AWSTools : public SysTools {
    public:
        enum AWSRegion {
            USEAST1, USWEST2, USWEST1, EUWEST1, EUCENTRAL1, APSOUTHEAST1, APSOUTHEAST2, APNORTHEAST1, SAEAST1
        };
        enum AWSInstanceState {
            pending = 0, running = 16, shutting_down = 32, terminated = 48, stopping = 64, stopped = 80
        };

        struct AWSInstance {
            std::string id;
            std::string publicIp;
            std::string publicDNSname;
            AWSInstanceState state;
            bool createdByCGOpt;
            bool isWorker;
            bool isMessageQueue;
        };

        AWSTools(const std::string &_awsAccessKey,
                 const std::string &_awsSecretAccessKey,
                 const AWSTools::AWSRegion _region = AWSRegion::EUCENTRAL1,
                 size_t _instanceCount = 1)
                : awsAccessKey(_awsAccessKey),
                  awsSecretAccessKey(_awsSecretAccessKey),
                  region(_region),
                  instanceCount(_instanceCount) {

            std::string loggerName{Config::loggerName()};
            this->_logger = spdlog::get(loggerName);
            if(!this->_logger){
                if(Config::fileLogging()){
                    this->_logger = spdlog::daily_logger_mt(loggerName, 0, 0);
                } else {
                    this->_logger = spdlog::stdout_logger_mt(loggerName);
                }
            }

            if(Config::verboseLogging()){
                this->_logger->set_level(spdlog::level::trace);
            }

            this->envString = "AWS_ACCESS_KEY_ID=" + awsAccessKey
                              + " AWS_SECRET_ACCESS_KEY=" + awsSecretAccessKey + " AWS_DEFAULT_REGION=" +
                              regionEnumStrings[region];
            this->ec2BaseCmd = envString + " /usr/local/bin/aws ec2 ";

            const char *homeDir = std::getenv("HOME");

            if (!homeDir) {
                struct passwd *pwd = getpwuid(getuid());
                if (pwd) {
                    homeDir = pwd->pw_dir;
                }
            }

            assert(homeDir != NULL && "Could not determine home directory, rerun with env variable HOME set." );

            this->home = std::string{homeDir};
            this->keyPath = {home+"/.cgopt/"};

            //check if aws cli is available
            //for whatever reason, the call will return 255 when debugging
            //so consider removing this assertion if need arises.
            int retCode;
            this->runCmd("aws help > /dev/null 2>&1", retCode);
            //assert(retCode == 0 && "awscli not found");

            this->myIp = this->getLocalIp();
            assert(myIp.size() > 0
                   && "Couldn't get this machines externally visible ip address. Are you connected to the internet?");

            _logger->info("AWSTools successfully initialized.");
        }

        void runSetup();

        std::vector<AWSInstance> getInstances() const;

        std::vector<std::string> startAndGetInstanceAddresses();

        void setTerminateOnExit(bool _terminateOnExit) { this->terminateOnExit = _terminateOnExit; };
        void setMessageQueueType(std::string serverType){ this->messageQueueAWSServerType = serverType; };
        void getGPUInstances();

        ~AWSTools() {
            shutdownInstances();
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
        const std::string secGroupName{"cgopt-sg"};
        const std::string keyName{"cgopt-key"};
        const std::string keyFileName{"cgopt-key.pem"};
        std::string home;       // in constructor
        std::string keyPath;    // in constructor
        std::string myIp;       // in constructor
        std::string messageQueueAWSServerType;

        std::shared_ptr<spdlog::logger> _logger;

        // PRIVATE DATA
        std::string awsAccessKey, awsSecretAccessKey, envString, ec2BaseCmd;
        AWSRegion region;
        size_t instanceCount;
        bool terminateOnExit = false;
        bool useSeparateServerForMsgQueue = false;
//        std::vector<AWSInstance> availableGPUInstances;
        std::vector<AWSInstance> workingSet;
        AWSInstance messageQueue;


        // Methods
        bool keyPresentLocally();
        bool remoteKeypairExists();
        void createSecGroup();
        void removeRemoteKeypair();
        std::vector<AWSInstance> getAvailableGPUInstances();
        void createAndStoreKeypair();
        void shutdownInstances();
        AWSInstance getMessageQueue();

        std::string getLocalIp() const;
        std::string runEC2Cmd(const std::string cmd) const;
        std::string runEC2Cmd(const std::string cmd, int &retCode) const;
        std::string getInstancesStringByType(const std::string type) const;
        std::vector<std::string> getSecurityGroupData() const;
        std::vector<std::string> getInstanceAddresses() const;
    };

}



