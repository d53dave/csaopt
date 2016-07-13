//
// Created by David on 01.05.2015.
//

#include <algorithm>
#include <fstream>
#include <vector>
#include <sstream>
#include <set>
#include "AWSTools.h"
#include "CSAOptInstance.h"

void sleepcp(int seconds){
    usleep(seconds * 1000 * 1000); //microsecs
}

namespace CSAOpt {
    std::string AWSTools::runEC2Cmd(std::string cmd) const {
        return runCmd(ec2BaseCmd + cmd);
    }

    std::string AWSTools::runEC2Cmd(std::string cmd, int &retCode) const {
        return runCmd(ec2BaseCmd + cmd, retCode);
    }



    void AWSTools::getGPUInstances() {
        std::vector<CSAOptInstance> availableGPUInstances = this->getAvailableGPUInstances();

        std::vector<CSAOptInstance> stoppedInstances;
        std::copy_if(availableGPUInstances.begin(), availableGPUInstances.end(), std::back_inserter(stoppedInstances),
                     [](CSAOptInstance const & x) { return x.state == AWSTools::stopped
                                                        || x.state == AWSTools::stopping; });

        std::vector<CSAOptInstance> runningInstances;
        std::copy_if(availableGPUInstances.begin(), availableGPUInstances.end(), std::back_inserter(runningInstances),
                     [](CSAOptInstance const & x) { return x.state == AWSTools::running; });

        std::set<std::string> instanceIds;
        size_t instancesToSpinUp = instanceCount - availableGPUInstances.size();
        assert(instancesToSpinUp >= 0 && instancesToSpinUp <= 20);

        _logger->info("Spinning up {} instances", instancesToSpinUp);

        if (instancesToSpinUp > 0) {
            picojson::value v;
            std::string groupsJson = runEC2Cmd(
                    "run-instances --image-id " + UBUNTU14_4_HVM_AMI + " --count " + std::to_string(instancesToSpinUp)
                    + " --instance-type " + T2_MICRO + " --key-name " + keyName + " --security-groups " + secGroupName);

            std::string err = picojson::parse(v, groupsJson);
            if (err.empty()) {
                picojson::array instanceList = v.get("Instances").get<picojson::array>();

                for (picojson::array::iterator iter = instanceList.begin(); iter != instanceList.end(); ++iter) {
                    std::string instanceId{(*iter).get("InstanceId").get<std::string>()};
                    _logger->info("Inserting instance id " + instanceId);
                    instanceIds.insert(instanceId);
                }
            } else {
                _logger->error(err);
            }

            sleepcp(5);
            while (!instanceIds.empty()) {
                sleepcp(5);
                std::ostringstream instancesStringStream;
                for (auto &name:instanceIds) {
                    instancesStringStream << name << ", ";
                }
                std::string instancesString = instancesStringStream.str();
                instancesString.erase(instancesString.length()-2); //remove last ', '

                _logger->info("Waiting for instances [{}] to become available", instancesString);
                getAvailableGPUInstances();
                //the following part is inefficient but the lists are small, so who gives?
                for (auto &i : availableGPUInstances) {
                    if (i.state == AWSInstanceState::running) {
                        auto a = instanceIds.find(i.id);
                        if (a != instanceIds.end()) {
                            instanceIds.erase(a);
                        }
                    }
                }
            }

        } else {
            _logger->error( "Tried to start less than 1 instance");
        }
    }

    std::string AWSTools::getInstancesStringByType(const std::string type) const {
        std::string cmd = "describe-instances --filters  "
                                  "\"Name=instance-type,Values="+ type +"\" "
                                  "\"Name=instance.group-name,Values=" + secGroupName + "\" ";
        std::string result = runEC2Cmd(cmd);

        return result;
    }


    std::vector<AWSInstance> AWSTools::getAvailableGPUInstances() {
        std::string result = this->getInstancesStringByType(G2_2X_LARGE + "," + G2_8X_LARGE);

        _logger->debug("AWSTools::getAvailableGPUInstances Result: {}", result);

        std::vector<AWSInstance> availableGPUInstances;

        picojson::value v;
        std::string err = picojson::parse(v, result);


        if (err.empty() && v.get("Reservations").is<picojson::array>()) {
            picojson::array reservationList = v.get("Reservations").get<picojson::array>();
            if (reservationList.size() > 0) {
                picojson::array instanceList = reservationList[0].get("Instances").get<picojson::array>();
                for (picojson::array::iterator iter = instanceList.begin(); iter != instanceList.end(); ++iter) {
                    int code = (*iter).get("State").get("Code").get<int64_t>();
                    AWSInstanceState state = static_cast<AWSInstanceState>(code);
                    std::string instanceId{(*iter).get("InstanceId").get<std::string>()};
                    std::string publicDnsName;
                    std::string publicIp;
                    if(state == AWSInstanceState::running){
                        publicDnsName = (*iter).get("PublicDnsName").get<std::string>();
                        publicIp = (*iter).get("PublicIpAddress").get<std::string>();
                    }

                    _logger->info("Processed Instance {} {} {} {}", instanceId, publicDnsName, publicIp, state);
                    availableGPUInstances.push_back({instanceId, publicIp, publicDnsName, state});
                }
            }
        } else {
            _logger->error( err);
        }
    }

    void AWSTools::createSecGroup() {
        _logger->info("Creating Sec Group");
        std::string result = runEC2Cmd("create-security-group --group-name " +
                secGroupName + " --description \"security group for cgopt\"");

        picojson::value v;
        std::string err = picojson::parse(v, result);

        _logger->debug(result);

        assert(err.empty() && v.get("GroupId").is<std::string>());

        int retCode;

        std::string authorizeGrp{
                "authorize-security-group-ingress --group-name " + secGroupName + " --protocol tcp --port 22 --cidr " +
                myIp + "/32"
        };

        std::string authGroupResult = runEC2Cmd(authorizeGrp, retCode);
        _logger->debug("Auth result: " + authGroupResult);
        assert(retCode == 0 && "Security Group authorization failed");
    }


    bool AWSTools::keyPresentLocally() {
        std::string fullPath = keyPath + keyFileName;

        std::ifstream t(fullPath);
        std::stringstream buffer;
        buffer << t.rdbuf();

        std::string token{"-----BEGIN RSA PRIVATE KEY-----"};
        return t.good() && buffer.str().find(token) != std::string::npos;
    };


    void AWSTools::createAndStoreKeypair() {
        _logger->info("Getting new keys...");
        std::string cmd = " create-key-pair --key-name " + keyName +
                          " --query 'KeyMaterial' --output text > " + keyFileName +
                          " && mkdir -p " + keyPath + " && mv " + keyFileName + " " + keyPath;

        runEC2Cmd(cmd);
        assert(keyPresentLocally() && "Key not found");
    }

    std::vector<std::string> AWSTools::getSecurityGroupData() const {
        auto vec = std::vector<std::string>();
        picojson::value v;
        std::string groupsJson = runEC2Cmd("describe-security-groups");

        std::string err = picojson::parse(v, groupsJson);
        if (err.empty()) {
            picojson::array list = v.get("SecurityGroups").get<picojson::array>();
            for (picojson::array::iterator iter = list.begin(); iter != list.end(); ++iter) {
                vec.push_back((*iter).get("GroupName").get<std::string>());
            }
        } else {
           _logger->error( err);
        }
        return vec;
    }

    std::vector<AWSTools::AWSInstance> AWSTools::getInstances() const {
        return workingSet;
    }

    std::vector<std::string> AWSTools::getInstanceAddresses() const{
        std::vector<std::string> addresses;
        for (auto &i : workingSet) {
            addresses.push_back(i.publicDNSname);
        }
        return addresses;
    }

    void AWSTools::runSetup() {
        _logger->info("Running AWS Setup");
        auto secData = getSecurityGroupData();

        for (auto &sec : secData) {
            _logger->debug("Secdata: " + sec);
        }

        if (secData.empty() || !std::any_of(secData.begin(), secData.end(),
                                            [this](std::string &grp) { return grp == secGroupName; })) {
            createSecGroup();
        } else {
            _logger->info("Secgroup found!");
        }

        if (remoteKeypairExists()) {
            _logger->info("Remote key found.");
            if (!keyPresentLocally()) { //generate new keys, local key is missing
                _logger->warn( "But we don't have local keys...");
                removeRemoteKeypair();
                createAndStoreKeypair();
            } else {
                _logger->info("Local key found.");
            }
        } else {
            if (keyPresentLocally()) {
                runCmd("rm -f " + keyPath + keyFileName);
                std::string msg = "Unable to delete local key at " + keyPath + keyFileName;
                assert(!keyPresentLocally() && msg.c_str());
            }
            createAndStoreKeypair();
        }

        getAvailableGPUInstances();
        if(useSeparateServerForMsgQueue){
            this->messageQueue = getMessageQueue();
        }

    }


    AWSInstance AWSTools::getMessageQueue() {
        std::string messageQueueServerType = messageQueueAWSServerType.empty() ? this->T2_SMALL
                                                                               : messageQueueServerType;

        std::string result = this->getInstancesStringByType(messageQueueServerType);

        picojson::value v;
        std::string err = picojson::parse(v, result);

        std::vector<AWSInstance> returnedInstances;

        if (err.empty() && v.get("Reservations").is<picojson::array>()) {
            picojson::array reservationList = v.get("Reservations").get<picojson::array>();
            if (reservationList.size() > 0) {
                picojson::array instanceList = reservationList[0].get("Instances").get<picojson::array>();
                for (picojson::array::iterator iter = instanceList.begin(); iter != instanceList.end(); ++iter) {
                    int code = (*iter).get("State").get("Code").get<int64_t>();
                    AWSInstanceState state = static_cast<AWSInstanceState>(code);
                    if (state == stopped || state == stopping || state == running) {
                        std::string instanceId{(*iter).get("InstanceId").get<std::string>()};
                        std::string publicDnsName;
                        std::string publicIp;
                        if (state == AWSInstanceState::running) {
                            publicDnsName = (*iter).get("PublicDnsName").get<std::string>();
                            publicIp = (*iter).get("PublicIpAddress").get<std::string>();
                        }

                        _logger->info("Processed Instance {} {} {} {}", instanceId, publicDnsName, publicIp, state);
                        returnedInstances.push_back({instanceId, publicIp, publicDnsName, state});
                    }
                }
            }
        } else {
            _logger->error(err);
        }
    }

    void AWSTools::removeRemoteKeypair() {
        _logger->info("Removing the remote key pair");
        std::string cmd = "delete-key-pair --key-name " + keyName;
        std::string returnVal = runEC2Cmd(cmd);
        assert(returnVal.empty()); //empty when successful
    }

    bool AWSTools::remoteKeypairExists() {
        std::string cmd = "describe-key-pairs";

        std::string result = runEC2Cmd(cmd);
        picojson::value v;

        std::string err = picojson::parse(v, result);
        if (err.empty()) {
            _logger->debug("Result: "+result);
            picojson::array list = v.get("KeyPairs").get<picojson::array>();
            for (picojson::array::iterator iter = list.begin(); iter != list.end(); ++iter) {
                if ((*iter).get("KeyName").get<std::string>() == keyName) {
                    return true;
                }
            }
        } else {
            _logger->error(err);
        }
        return false;
    }

    void AWSTools::shutdownInstances() {
        if(useSeparateServerForMsgQueue){
            std::ostringstream shutdownCmd;
            const char * logMsgFmt;
            if(terminateOnExit){
                logMsgFmt = "Terminating instances {}";
                shutdownCmd << "terminate-instances ";
            } else {
                logMsgFmt = "Stopping MessageQueue {}";
                shutdownCmd << "stop-instances ";
            }
            shutdownCmd << "--instance-ids " << messageQueue.id;
            _logger->info(logMsgFmt, messageQueue.id);
            runEC2Cmd(shutdownCmd.str());
        }

        if (!workingSet.empty()) {

            std::ostringstream shutdownCmd;
            std::ostringstream joinedIds;

            const char * logMsgFmt;

            for (auto &i : workingSet) {
                joinedIds << " " + i.id;
            }

            if (terminateOnExit) {
                logMsgFmt = "Terminating instances {}";
                shutdownCmd << "terminate-instances ";
            } else {
                logMsgFmt = "Stopping instances {}";
                shutdownCmd << "stop-instances ";
            }

            std::string joinedIdsString = joinedIds.str();
            shutdownCmd << "--instance-ids" << joinedIdsString;

            _logger->info(logMsgFmt, joinedIdsString);
            runEC2Cmd(shutdownCmd.str());
        } else {
            _logger->info("No instances to shutdown/terminate.");
        }
        //runEC2Cmd("delete-security-group --group-name "+secGroupName);
    }

    std::string AWSTools::getLocalIp() const {
        int retCode;
        std::string myIp = runCmd("curl http://checkip.amazonaws.com/ 2>/dev/null", retCode);
        if(retCode > 0){ //try something else
            myIp = runCmd("wget -qO- http://checkip.amazonaws.com/ 2>/dev/null", retCode);
        }
        myIp.erase(std::remove(myIp.begin(), myIp.end(), '\n'), myIp.end());
        return myIp;
    }
}