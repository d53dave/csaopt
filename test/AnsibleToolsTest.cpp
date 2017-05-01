//
// Created by David Sere on 12/10/15.
//

#include "TestConfig.h"
#include <fstream>
#include <vector>
#include <sstream>
#include <string>
#include <algorithm>
#include "../src/AWS/AWSTools.h"
#include "../src/AnsibleTools.h"

void assertFile(std::string hostsFilePath, std::vector<std::string> ipAddresses, std::string messageQueueIp){
    std::ifstream infile(hostsFilePath);
    std::string line;
    bool processingWorkers = false;
    bool processingMessageQueue = false;
    int workerCount = 0;
    while (std::getline(infile, line))
    {
        if(line.compare("[worker]") == 0) {
            processingWorkers = true;
            processingMessageQueue = false;
        } else if(line.compare("[msgqueue]") == 0){
            processingWorkers = false; processingMessageQueue = true;
        } else if(processingWorkers){
            workerCount += 1;
            REQUIRE( std::find(ipAddresses.begin(), ipAddresses.end(), line) != ipAddresses.end() );
            continue;
        } else if(processingMessageQueue){
            REQUIRE( messageQueueIp.compare( line ) == 0 );
        }
    }
    REQUIRE( workerCount == ipAddresses.size() );
}


TEST_CASE("AnsibleToolsTest", "[Ansible]"){
    SECTION("The hosts file is written correctly when msgqueue is on a worker") {
        std::string hostsFilePath = "./hosts";
        CSAOpt::AnsibleTools ansibleTools;
        ansibleTools.setHostsFilePath(hostsFilePath);

        using CSAOpt::CSAOptInstance;
        std::vector<CSAOptInstance> instanceVector;
        instanceVector.push_back(CSAOptInstance{"testid1", "1.2.3.4", "dnsname1", CSAOptInstance::InstanceState::running, true, true});
        instanceVector.push_back(CSAOptInstance{"msgqueueworker", "1.2.3.5", "dnsname2", CSAOptInstance::InstanceState::running, true, true});
        instanceVector.push_back(CSAOptInstance{"testid3", "1.2.3.6", "dnsname3", CSAOptInstance::InstanceState::running, true, true});

        std::vector<std::string> ipAddresses;

        std::transform(instanceVector.begin(),
                       instanceVector.end(),
                       std::back_inserter(ipAddresses),
                       [](CSAOpt::CSAOptInstance i) {return i.publicIp;} );

        std::string messageQueueIp = instanceVector[1].publicIp;

        ansibleTools.writeHostsFile(instanceVector);
        assertFile(hostsFilePath, ipAddresses, messageQueueIp);
    }

    SECTION("The hosts file is written correctly when separate messagequeue instance") {
        std::string hostsFilePath = "./hosts";
        CSAOpt::AnsibleTools ansibleTools;
        ansibleTools.setHostsFilePath(hostsFilePath);

        using CSAOpt::CSAOptInstance;
        std::vector<CSAOptInstance> instanceVector;
        instanceVector.push_back(CSAOptInstance{"testid4", "1.2.3.7", "dnsname4", CSAOptInstance::InstanceState::running, true, true});
        instanceVector.push_back(CSAOptInstance{"testid5", "1.2.3.8", "dnsname5", CSAOptInstance::InstanceState::running, true, true});
        instanceVector.push_back(CSAOptInstance{"msgqueue", "1.2.3.9", "dnsname6",CSAOptInstance::InstanceState::running, true, false});


        std::vector<std::string> ipAddresses;

        std::transform(instanceVector.begin(),
                       instanceVector.end(),
                       std::back_inserter(ipAddresses),
                       [](CSAOptInstance i) {return i.publicIp;} );

        std::string messageQueueIp = instanceVector[2].publicIp;

        ansibleTools.writeHostsFile(instanceVector);

        ipAddresses.erase(ipAddresses.end()-1);
        assertFile(hostsFilePath, ipAddresses, messageQueueIp);
    }
}
