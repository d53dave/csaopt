//
// Created by David Sere on 28/09/15.
//


#include <iostream>
#include <stdlib.h>
#include <pwd.h>
#include <unistd.h>
#include "picojson/picojson.h"
#include "SysTools.h"
#include "spdlog/spdlog.h"

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
        };

        void log(std::string s) {

        }

        AWSTools(const std::string &_awsAccessKey,
                 const std::string &_awsSecretAccessKey,
                 const AWSTools::AWSRegion _region = AWSRegion::EUWEST1,
                 size_t _instanceCount = 1)
                : awsAccessKey(_awsAccessKey),
                  awsSecretAccessKey(_awsSecretAccessKey),
                  region(_region),
                  instanceCount(_instanceCount) {

            this->_logger = spdlog::get("console");
            if(!this->_logger){
                this->_logger = spdlog::stdout_logger_mt("console");
            }

            this->envString = "AWS_ACCESS_KEY_ID=" + awsAccessKey
                              + " AWS_SECRET_ACCESS_KEY=" + awsSecretAccessKey + " AWS_DEFAULT_REGION=" +
                              regionEnumStrings[region];
            this->ec2BaseCmd = envString + " /usr/local/bin/aws ec2 ";

            const char *homeDir = getenv("HOME");

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
            int retCode;
            this->runCmd("aws help > /dev/null 2>&1", retCode);
            assert(retCode == 0 && "awscli not found");

            runSetup();


            log("Setup finished");
        }

        std::vector<AWSInstance> getInstances();

        std::vector<std::string> startAndGetInstanceAddresses();

        void setTerminateOnExit(bool _terminateOnExit) { this->terminateOnExit = _terminateOnExit; };

        void startGPUInstances();

        ~AWSTools() {
            std::cout << "AWSTOOLS DTOR" << std::endl;
            shutdownInstances();
        };

    private:

        // STRINGS
        const std::string regionEnumStrings[10] = {"us-east-1", "us-west-2", "us-west-1", "eu-west-1", "eu-central-1",
                                                   "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "sa-east-1"};
        const std::string UBUNTU14_4_HVM_AMI{"ami-47a23a30"};
        const std::string CUDA_AMI{"ami-f88281e5"};
        const std::string G2_2X_LARGE{"g2.2xlarge"};
        const std::string T2_MICRO{"t2.micro"};
        const std::string secGroupName{"cgopt-sg"};
        const std::string keyName{"cgopt-key"};
        const std::string keyFileName{"cgopt-key.pem"};
        std::string home; // in constructor
        std::string keyPath; // in constructor

        std::shared_ptr<spdlog::logger> _logger;


        // PRIVATE DATA
        std::string awsAccessKey, awsSecretAccessKey, envString, ec2BaseCmd;
        AWSRegion region = EUWEST1;
        size_t instanceCount;
        bool terminateOnExit = false;
        std::vector<AWSInstance> awsInstances;


        // Methods
        bool keyPresentLocally();

        bool awsKeypairExists();

        void runSetup();

        void createSecGroup();

        void removeRemoteKeypair();

        void getAvailableInstances();

        void createAndStoreKeypair();

        void shutdownInstances();

        std::string runEC2Cmd(const std::string cmd) const;

        std::vector<std::string> getSecurityGroupData() const;

        std::vector<std::string> getInstanceAddresses() const;
    };

}



