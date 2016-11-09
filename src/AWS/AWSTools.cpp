//
// Created by David on 01.05.2015.
//

#include <algorithm>
#include <fstream>
#include <vector>
#include <sstream>
#include <set>
#include <stdexcept>
#include <aws/ec2/model/DescribeInstancesRequest.h>
#include <aws/ec2/model/RunInstancesRequest.h>
#include <aws/core/auth/AWSCredentialsProvider.h>
#include <aws/ec2/model/DescribeInstanceStatusRequest.h>
#include <aws/ec2/model/DescribeAddressesRequest.h>
#include <aws/ec2/model/TerminateInstancesRequest.h>
#include <aws/ec2/model/CreateKeyPairRequest.h>
#include <aws/ec2/model/CreateSecurityGroupRequest.h>
#include "AWSTools.h"
#include "Utils.h"
#include "CSAOptInstance.h"

namespace CSAOpt {




    AWSTools::AWSTools(const std::string &_awsAccessKey, const std::string &_awsSecretAccessKey,
                       const AWSRegion _region, size_t _instanceCount)
            : awsAccessKey(_awsAccessKey),
              awsSecretAccessKey(_awsSecretAccessKey),
              region(_region),
              instanceCount(_instanceCount) {
        setupLogger();

        std::string homeDir = getHomeDir();

        if (homeDir.empty()) {
            std::string msg = "Could not determine home directory, rerun with env variable HOME set.";
            this->_logger->error(msg);
            throw std::runtime_error(msg);
        };

        this->home = std::string{homeDir};
        this->trackingTag = randomString(10);
        this->keyName = {"csaopt" + this->trackingTag + ".pem"};
        this->keyPath = {home + "/.csaopt/" + this->keyName};
        this->secGroupName = {"csaopt-sg-" + trackingTag};

        this->myIp = this->getLocalIp();
        if (myIp.empty()) {
            std::string msg = "Couldn't get this machines externally visible ip address. Are you connected to the internet?";
            this->_logger->error(msg);
            throw std::runtime_error(msg);
        };

        _logger->info("AWSTools successfully initialized.");
    }

    WorkingSet AWSTools::startInstances(int instanceCount, Aws::EC2::Model::InstanceType instanceType,
                              Aws::EC2::EC2Client &client) {
        Aws::EC2::Model::RunInstancesRequest request;

        request
                .WithDryRun(false)
                .WithImageId("ami-f88281e5")
                .WithMinCount(instanceCount)
                .WithMaxCount(instanceCount)
                .WithInstanceType(instanceType);

        WorkingSet instances;

        auto runInstances = client.RunInstances(request);

        if (runInstances.IsSuccess()) {
            auto result = runInstances.GetResult();
            std::cout << "Sucess" << std::endl;
            int i = 0;
            for (auto &&instance : result.GetInstances()) {
                std::cout << "Instance " << i++ << ": " << instance.GetInstanceId() << std::endl;
                auto csaOptInst = mapEC2Instance(instance);
                instances[csaOptInst.id] = csaOptInst;
            }
        } else {
            auto error = runInstances.GetError();
            std::cout << "Error: " << error.GetMessage() << std::endl;
            throw std::runtime_error("Error while staring instances: " + error.GetMessage());
        }

        return instances;
    }

    std::string AWSTools::createSecGroup(std::string name, Aws::EC2::EC2Client &client) {
        Aws::EC2::Model::CreateSecurityGroupRequest createSecurityGroupRequest;

        auto secGroupResponse = client.CreateSecurityGroup(createSecurityGroupRequest.WithGroupName(name));

        if (secGroupResponse.IsSuccess()) {
            return secGroupResponse.GetResult().GetGroupId();
        } else {
            auto error = secGroupResponse.GetError();
            std::cerr << "CreateSecurityGroup call failed with error" << error.GetExceptionName()
            << " and message " << error.GetMessage() << std::endl;
            throw std::runtime_error("CreateSecurityGroup call failed with error '" + error.GetExceptionName()
                                     + "' and message: " + error.GetMessage());
        }
    }

    bool AWSTools::keyPresentLocally(std::string path) {

        std::ifstream t(path);
        std::stringstream buffer;
        buffer << t.rdbuf();

        std::string tokenBegin{"-----BEGIN RSA PRIVATE KEY-----"};
        std::string tokenEnd{"-----END RSA PRIVATE KEY-----"};
        return t.good()
               && buffer.str().find(tokenBegin) != std::string::npos
               && buffer.str().find(tokenEnd) != std::string::npos;
    };


    std::string AWSTools::getKeyMaterial(std::string name, Aws::EC2::EC2Client &client) {
        _logger->info("Getting new keys...");

        Aws::EC2::Model::CreateKeyPairRequest createKeyPairRequest;

        auto keyPairResponse = client.CreateKeyPair(createKeyPairRequest.WithKeyName(name));

        if (keyPairResponse.IsSuccess()) {
            return keyPairResponse.GetResult().GetKeyMaterial();
        } else {
            auto error = keyPairResponse.GetError();
            std::cerr << "CreateSecurityGroup call failed with error" << error.GetExceptionName()
            << " and message " << error.GetMessage() << std::endl;
            throw std::runtime_error("CreateSecurityGroup call failed with error '" + error.GetExceptionName()
                                     + "' and message: " + error.GetMessage());
        }
    }

    std::map<InstanceId, CSAOptInstance> AWSTools::getInstances() const {
        return workingSet;
    }

    void AWSTools::waitUntilRunning(const std::vector<Aws::String> instanceIds, Aws::EC2::EC2Client &client) const {
        Aws::EC2::Model::DescribeInstanceStatusRequest instanceStatusRequest;
        instanceStatusRequest.SetInstanceIds(instanceIds);

        auto describeStatuses = client.DescribeInstanceStatus(instanceStatusRequest);

        if (describeStatuses.IsSuccess()) {
            auto states = describeStatuses.GetResult().GetInstanceStatuses();

            while (std::any_of(states.cbegin(), states.cend(),
                               [](const Aws::EC2::Model::InstanceStatus &state) {
                                   return state.GetInstanceState().GetName() !=
                                          Aws::EC2::Model::InstanceStateName::running;
                               }) || states.size() < instanceIds.size()) {
                std::this_thread::sleep_for(std::chrono::seconds(5));
                std::cout << "Still waiting for instances to spin up." << std::endl;
                states = client.DescribeInstanceStatus(instanceStatusRequest).GetResult().GetInstanceStatuses();
            }
        } else {
            auto error = describeStatuses.GetError();
            std::cout << "Error: " << error.GetMessage() << std::endl;
            throw std::runtime_error("Error while waiting for instances to start: " + error.GetMessage());
        }
    }

    std::map<InstanceId, std::string>  AWSTools::getInstanceAddresses(const WorkingSet &instances,
                                                                      Aws::EC2::EC2Client &client) const {
        std::vector<std::string> instanceIds;

        for (auto &&instance : instances) {
            instanceIds.push_back(instance.first); // first is InstanceId, second is the actual instance
        }

        Aws::EC2::Model::DescribeInstancesRequest describeInstancesRequest;
        describeInstancesRequest.WithInstanceIds(instanceIds);

        std::map<InstanceId, std::string> instanceIps;

        while (instanceIps.size() < instanceIds.size()) {
            auto describeResult = client.DescribeInstances(describeInstancesRequest);

            if (describeResult.IsSuccess()) {
                auto result = describeResult.GetResult();
                result.GetReservations()[0].GetInstances()[0].GetPublicIpAddress();

                for (auto &&reservation : describeResult.GetResult().GetReservations()) {
                    for (auto &instance : reservation.GetInstances()) {

                        instance.GetPublicIpAddress();
                        instanceIps.emplace(instance.GetInstanceId(), instance.GetPublicIpAddress());
                        std::this_thread::sleep_for(std::chrono::seconds(5));
                    }
                }
                std::cout << "Still waiting for public ips" << std::endl;
            } else {
                auto error = describeResult.GetError();
                std::cerr << "DescribeInstances call failed with error" << error.GetExceptionName()
                << " and message " << error.GetMessage() << std::endl;
                throw std::runtime_error("DescribeInstances call failed with error '" + error.GetExceptionName()
                                         + "' and message: " + error.GetMessage());

            }
        }
        return instanceIps;
    }

    void AWSTools::runSetup() {
        _logger->info("Running AWS Setup");

        std::string accessKey = "";
        std::string accessSecret = "";

        Aws::SDKOptions options;
        options.loggingOptions.logLevel = Aws::Utils::Logging::LogLevel::Debug;
        Aws::InitAPI(options);


        Aws::Auth::AWSCredentials credentials(Aws::String(accessKey.c_str()), Aws::String(accessSecret.c_str()));

        Aws::Client::ClientConfiguration configuration;
        configuration.region = Aws::Region::EU_CENTRAL_1;

        Aws::EC2::EC2Client client(credentials, configuration);

        this->createSecGroup(this->secGroupName, client);

        std::string keymaterial = this->getKeyMaterial(this->keyName, client);

        if (useSeparateMachineAsMsgQueue) {
            this->startInstances(1, mapType(this->messageQueueAWSServerType), client);
            this->messageQueue = getMessageQueue();
        }

    }


    CSAOptInstance &AWSTools::getMessageQueue() {
        for (auto &&kvp : this->workingSet) {
            if (kvp.second.isMessageQueue) {
                return kvp.second;
            }
        }
        throw std::runtime_error("AWSTools::getMessageQueue() could not find MessageQueue in working set");
    }


    void AWSTools::shutdown(Aws::EC2::EC2Client &client) {
        std::vector<InstanceId> idsToShutdown;
        if (useSeparateMachineAsMsgQueue) {
            idsToShutdown.push_back(this->getMessageQueue().id);
        }

        for (auto &&instance : this->workingSet) {
            idsToShutdown.push_back(instance.first);
        }

        Aws::EC2::Model::TerminateInstancesRequest terminateInstancesRequest;

        while (idsToShutdown.size() > 0) {
            auto terminateResponse =
                    client.TerminateInstances(terminateInstancesRequest.WithInstanceIds(idsToShutdown));
            if (terminateResponse.IsSuccess()) {
                auto result = terminateResponse.GetResult();
                for (auto &&instance : result.GetTerminatingInstances()) {
                    this->workingSet[instance.GetInstanceId()].state = mapState(instance.GetCurrentState());
                }
            } else {
                auto error = terminateResponse.GetError();
                std::cerr << "TerminateInstances call failed with error" << error.GetExceptionName()
                << " and message " << error.GetMessage() << std::endl;
                throw std::runtime_error("TerminateInstances call failed with error '" + error.GetExceptionName()
                                         + "' and message: " + error.GetMessage());
            }
        }
    }

    std::string AWSTools::getLocalIp() const {
        int retCode;
        std::string myIp = runCmd("curl http://checkip.amazonaws.com/ 2>/dev/null", retCode);
        if (retCode > 0) { //try something else
            myIp = runCmd("wget -qO- http://checkip.amazonaws.com/ 2>/dev/null", retCode);
        }
        myIp.erase(std::remove(myIp.begin(), myIp.end(), '\n'), myIp.end());
        return myIp;
    }


    void AWSTools::setupLogger() {
        std::string loggerName{Config::loggerName()};
        this->_logger = spdlog::get(loggerName);
        if (!this->_logger) {
            if (Config::fileLogging()) {
                this->_logger = spdlog::daily_logger_mt(loggerName, 0, 0);
            } else {
                this->_logger = spdlog::stdout_logger_mt(loggerName);
            }
        }

        if (Config::verboseLogging()) {
            this->_logger->set_level(spdlog::level::trace);
        }
    }
}