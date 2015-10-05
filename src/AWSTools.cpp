//
// Created by David on 01.05.2015.
//

#include <assert.h>
#include <fstream>
#include <vector>
#include <sstream>
#include <set>
#include "AWSTools.h"

#include <iostream>
#include <unistd.h>



void sleepcp(int seconds){
    std::cout << "Going to sleep...";
    std::cout.flush();
    usleep(seconds * 1000 * 1000); //microsecs
    std::cout << " woke up"<<std::endl;
}

namespace CGOpt {
    std::string AWSTools::runEC2Cmd(std::string cmd) const {
        return runCmd(ec2BaseCmd + cmd);
    }

    void AWSTools::startGPUInstances() {
        std::set<std::string> instanceIds;
        size_t instancesToSpinUp = instanceCount - awsInstances.size();
        assert(instancesToSpinUp >= 0 && instancesToSpinUp <= 5);

        std::cout << "Spinning up " << instancesToSpinUp << " instances" << std::endl;

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
                    std::cout << "Inserting instance id " + instanceId << std::endl;
                    instanceIds.insert(instanceId);
                }
            } else {
                std::cerr << err << std::endl;
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

                std::cout << "Waiting for instances [" + instancesString + "] to become available" << std::endl;
                getAvailableInstances();
                //the following code is inefficient but the lists are small, so who gives?
                for (auto &i : awsInstances) {
                    if (i.state == AWSInstanceState::running) {
                        auto a = instanceIds.find(i.id);
                        if (a != instanceIds.end()) {
                            instanceIds.erase(a);
                        }
                    }
                }
            }

        } else {
            std::cerr << "Tried to start less than 1 instance";
        }
    }


    void AWSTools::getAvailableInstances() {
        std::string cmd = "describe-instances --filters \"Name=instance.group-name,Values=" + secGroupName + "\"";
        std::string result = runEC2Cmd(cmd);

        awsInstances.clear();

        picojson::value v;
        std::string err = picojson::parse(v, result);


        if (err.empty() && v.get("Reservations").is<picojson::array>()) {
            picojson::array reservationList = v.get("Reservations").get<picojson::array>();
            if (reservationList.size() > 0) {
                picojson::array instanceList = reservationList[0].get("Instances").get<picojson::array>();
                for (picojson::array::iterator iter = instanceList.begin(); iter != instanceList.end(); ++iter) {
                    double code = (*iter).get("State").get("Code").get<double>();
                    std::string instanceId{(*iter).get("InstanceId").get<std::string>()};
                    std::string publicDnsName{(*iter).get("PublicDnsName").get<std::string>()};
                    std::string publicIp{(*iter).get("PublicIpAddress").get<std::string>()};
                    AWSInstanceState state = static_cast<AWSInstanceState>(static_cast<int>(code));
                    std::cout << "Processed Instance " << instanceId << " " << publicIp << " " << state << std::endl;
                    awsInstances.push_back({instanceId, publicIp, publicDnsName, state});
                }
            }
        } else {
            std::cerr << err << std::endl;
        }
    }

    void AWSTools::createSecGroup() {
        std::cout << "Creating Sec Group" << std::endl;
        std::string createSecGroupCommand{
                "create-security-group --group-name " + secGroupName + " --description \"security group for cgopt\""};
        std::string result = runEC2Cmd(createSecGroupCommand);

        picojson::value v;
        std::string err = picojson::parse(v, result);

        std::cout << result;

        assert(err.empty() && v.get("GroupId").is<std::string>());


        std::string myIp = runCmd("curl http://checkip.amazonaws.com/");
        myIp.erase(std::remove(myIp.begin(), myIp.end(), '\n'), myIp.end());
        std::string authorizeGrp{
                "authorize-security-group-ingress --group-name " + secGroupName + " --protocol tcp --port 22 --cidr " +
                myIp + "/32"
        };

        std::string authGroupResult = runEC2Cmd(authorizeGrp);
        std::cout << "Auth result: " << authGroupResult << std::endl;
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
        std::cout << "Getting new keys..." << std::endl;
        std::string cmd = " create-key-pair --key-name " + keyName +
                          " --query 'KeyMaterial' --output text > " + keyFileName +
                          " && mkdir -p " + keyPath + " && mv " + keyFileName + " " + keyPath;

        runEC2Cmd(cmd);
        std::cout << "Asserting keys good ..." << std::endl;
        assert(keyPresentLocally());
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
            std::cerr << err << std::endl;
        }
        return vec;
    }

    std::vector<AWSTools::AWSInstance> AWSTools::getInstances() {
        return awsInstances;
    }

    std::vector<std::string> AWSTools::getInstanceAddresses() const{
        std::vector<std::string> addresses;
        for (auto &i : awsInstances) {
            addresses.push_back(i.publicDNSname);
        }
        return addresses;
    }

    void AWSTools::runSetup() {
        std::cout << "Running setup!" << std::endl;
        auto secData = getSecurityGroupData();

        for (auto &sec : secData) {
            std::cout << "Secdata: " << sec << std::endl;
        }

        if (secData.empty() || !std::any_of(secData.begin(), secData.end(),
                                            [this](std::string &grp) { return grp == secGroupName; })) {
            createSecGroup();
        } else {
            std::cout << "Secgroup found!" << std::endl;
        }

        if (awsKeypairExists()) {
            std::cout << "We have remote keys..." << std::endl;
            if (!keyPresentLocally()) { //generate new keys, local key is missing
                std::cout << "But we don't have local keys..." << std::endl;
                removeRemoteKeypair();
                createAndStoreKeypair();
            };
        } else {
            if (keyPresentLocally()) {
                runCmd("rm -f " + keyPath + keyFileName);
                std::string msg = "Unable to delete local key at " + keyPath + keyFileName;
                assert(!keyPresentLocally() && msg.c_str());
            }
            createAndStoreKeypair();
        }

        getAvailableInstances();
    }

    void AWSTools::removeRemoteKeypair() {
        std::cout << "Removing the remote key pair" << std::endl;
        std::string cmd = "delete-key-pair --key-name " + keyName;
        std::string returnVal = runEC2Cmd(cmd);
        assert(returnVal.empty()); //empty when successful
    }

    bool AWSTools::awsKeypairExists() {
        std::string cmd = "describe-key-pairs";

        std::string result = runEC2Cmd(cmd);
        picojson::value v;

        std::string err = picojson::parse(v, result);
        if (err.empty()) {
            std::cout << result << std::endl;
            picojson::array list = v.get("KeyPairs").get<picojson::array>();
            for (picojson::array::iterator iter = list.begin(); iter != list.end(); ++iter) {
                if ((*iter).get("KeyName").get<std::string>() == keyName) {
                    return true;
                }
            }
        } else {
            std::cerr << err << std::endl;
        }
        return false;
    }

    void AWSTools::shutdownInstances() {
        if (!awsInstances.empty()) {
            std::ostringstream shutdownCmd;
            std::ostringstream joinedIds;

            for (auto &i : awsInstances) {
                joinedIds << " " + i.id;
            }

            if (terminateOnExit) {
                shutdownCmd << "terminate-instances --instance-ids";
            } else {
                shutdownCmd << "stop-instances --instance-ids";
            }
            shutdownCmd << joinedIds.str();
            runEC2Cmd(shutdownCmd.str());
        }

        //runEC2Cmd("delete-security-group --group-name "+secGroupName);
    }
}