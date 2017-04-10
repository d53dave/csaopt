//
// Created by David on 01.05.2015.
//

#include <algorithm>
#include <fstream>
#include <vector>
#include <sstream>
#include <set>
#include <thread>
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
                                        const Aws::EC2::EC2Client &client) {
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
            std::string msg = fmt::format("RunInstances call failed with error {} and message {}",
            error.GetExceptionName().c_str(), error.GetMessage().c_str());
            this->_logger->error(msg);
            throw std::runtime_error(msg);
        }

        return instances;
    }

    std::string AWSTools::createSecGroup(std::string name, Aws::EC2::EC2Client &client) {
        Aws::EC2::Model::CreateSecurityGroupRequest createSecurityGroupRequest;

        auto secGroupResponse = client.CreateSecurityGroup(createSecurityGroupRequest.WithGroupName(name.c_str()));

        if (secGroupResponse.IsSuccess()) {
            return secGroupResponse.GetResult().GetGroupId().c_str();
        } else {
            auto error = secGroupResponse.GetError();
            std::string msg = fmt::format("CreateSecurityGroup call failed with error {} and message {}",
                    error.GetExceptionName().c_str(), error.GetMessage().c_str());
            this->_logger->error(msg);
            throw std::runtime_error(msg);
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
        _logger->info("Getting keys...");

        Aws::EC2::Model::CreateKeyPairRequest createKeyPairRequest;

        auto keyPairResponse = client.CreateKeyPair(createKeyPairRequest.WithKeyName(name.c_str()));

        if (keyPairResponse.IsSuccess()) {
            return keyPairResponse.GetResult().GetKeyMaterial().c_str();
        } else {
            auto error = keyPairResponse.GetError();
            std::string msg = fmt::format("CreateKeyPair call failed with error {} and message {}",
            error.GetExceptionName().c_str(), error.GetMessage().c_str());
            this->_logger->error(msg);
            throw std::runtime_error(msg);
        }
    }

    std::map<InstanceId, CSAOptInstance> AWSTools::getInstances() const {
        return workingSet;
    }

    void AWSTools::waitUntilRunning(std::vector<Aws::String> instanceIds, Aws::EC2::EC2Client &client) const {
        Aws::EC2::Model::DescribeInstanceStatusRequest instanceStatusRequest;

        Aws::Vector<Aws::String> ids;
        for(auto &&id : instanceIds) {
            ids.push_back(id);
        }

        instanceStatusRequest.SetInstanceIds(ids);

        auto describeStatuses = client.DescribeInstanceStatus(instanceStatusRequest);

        if (describeStatuses.IsSuccess()) {
            auto states = describeStatuses.GetResult().GetInstanceStatuses();
            size_t retries = 0;

            while (std::any_of(states.cbegin(), states.cend(),
                               [](const Aws::EC2::Model::InstanceStatus &state) {
                                   return state.GetInstanceState().GetName() !=
                                          Aws::EC2::Model::InstanceStateName::running;
                               }) || states.size() < instanceIds.size()) {
                std::this_thread::sleep_for(std::chrono::seconds(this->waitIntervalSeconds));
                this->_logger->info("Still waiting for instances to spin up...");
                states = client.DescribeInstanceStatus(instanceStatusRequest).GetResult().GetInstanceStatuses();
                if (retries++ >= this->maxRetries) {
                    this->_logger->error("Unsuccessfully Waited for {} seconds for all Instances to start. Aborting.",
                                         maxRetries * this->waitIntervalSeconds);

                    throw std::runtime_error("Maxretries reached.");
                }
            }
        } else {
            auto error = describeStatuses.GetError();
            std::string msg = fmt::format("DescribeInstanceStatus call failed with error '{}' and message: {}",
            error.GetExceptionName().c_str(), error.GetMessage().c_str());
            this->_logger->error(msg);

            throw std::runtime_error(msg);
        }
    }

    std::map<InstanceId, Aws::String>  AWSTools::getInstanceAddresses(const WorkingSet &instances,
                                                                      Aws::EC2::EC2Client &client) const {
        Aws::Vector<InstanceId> instanceIds;

        for (auto &&instance : instances) {
            instanceIds.push_back(instance.first); // first is InstanceId, second is the actual instance
        }

        Aws::EC2::Model::DescribeInstancesRequest describeInstancesRequest;
        describeInstancesRequest.WithInstanceIds(instanceIds);

        std::map<InstanceId, Aws::String> instanceIps;

        while (instanceIps.size() < instanceIds.size()) {
            auto describeResult = client.DescribeInstances(describeInstancesRequest);

            if (describeResult.IsSuccess()) {
                auto result = describeResult.GetResult();
                result.GetReservations()[0].GetInstances()[0].GetPublicIpAddress();

                for (auto &&reservation : describeResult.GetResult().GetReservations()) {
                    for (auto &instance : reservation.GetInstances()) {

                        instance.GetPublicIpAddress();
                        std::pair<InstanceId, Aws::String> instanceWithIp(instance.GetInstanceId(), instance.GetPublicIpAddress());
                        instanceIps.emplace(instanceWithIp);
                        std::this_thread::sleep_for(std::chrono::seconds(5));
                    }
                }
                std::cout << "Still waiting for public ips" << std::endl;
            } else {
                auto error = describeResult.GetError();
                std::cerr << "DescribeInstances call failed with error" << error.GetExceptionName()
                << " and message " << error.GetMessage() << std::endl;
                std::string msg = fmt::format("DescribeInstances call failed with error '{}' and message: {}",
                                              error.GetExceptionName().c_str(), error.GetMessage().c_str());

                throw std::runtime_error(msg);

            }
        }
        return instanceIps;
    }


    void writeKeyMaterial(std::string material, std::string path) {
        std::ofstream ofstream(path);
        ofstream << material;
        ofstream.close();
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
        if (keymaterial.empty()) {
            throw std::runtime_error("Could not retrieve keys");
        }

        writeKeyMaterial(keymaterial, this->keyPath);

        if (!this->keyPresentLocally(this->keyPath)) {
            throw std::runtime_error("Could not store key material");
        }

        this->createWorkerThread = std::thread([=] {
            std::stringstream ss;
            ss << std::this_thread::get_id();
            this->_logger->debug("Thread[{}] started. Creating workers.", ss.str());
            auto workingset = startInstances(2, mapType(this->T2_MICRO), client);
        });

        if (useSeparateMachineAsMsgQueue) {
            this->createMessageQueueThread = std::thread([=] {
                std::stringstream ss;
                ss << std::this_thread::get_id();
                this->_logger->debug("Thread[{}] started. Creating messagequeue.", ss.str());
                auto workingset = startInstances(1, mapType(this->messageQueueAWSServerType), client);
                this->messageQueue = getMessageQueue();
            });

            this->createMessageQueueThread.join();
        }
        this->createWorkerThread.join();

    }

    AWSTools::~AWSTools() {
        this->stopThreads = true;

        bool printNotice = false;
        for (auto &&kvp : this->workingSet) {
            if (kvp.second.state == CSAOptInstance::InstanceState::running) {
                _logger->warn("AWSTools is shutting down but instance with id {} is still running.", kvp.first.c_str());
                printNotice = true;
            }
        }

        if (printNotice) {
            _logger->warn("ATTENTION: It appears that not all instances could be stopped/terminated.\n"
                                  "Please verify the state of the instances in your AWS console and manually"
                                  "turn off instances that were left behind. Sorry :/");
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
        Aws::Vector<InstanceId> idsToShutdown;
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
                std::string msg = fmt::format("TerminateInstances call failed with error '{}' and message {}",
                                              error.GetExceptionName().c_str(), error.GetMessage().c_str());
                throw std::runtime_error(msg);
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