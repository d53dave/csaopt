//
// Created by David Sere on 12/10/15.
//

#include "TestConfig.h"
#include <fstream>
#include <vector>
#include <sstream>
#include <string>
#include <algorithm>
#include "../src/AWSTools.h"
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
        CGOpt::AnsibleTools ansibleTools;
        ansibleTools.setHostsFilePath(hostsFilePath);

        std::vector<CGOpt::AWSTools::AWSInstance> instanceVector;
        instanceVector.push_back({"testid1", "1.2.3.4", "dnsname1", CGOpt::AWSTools::running, true, true, false});
        instanceVector.push_back({"msgqueueworker", "1.2.3.5", "dnsname2", CGOpt::AWSTools::running, true, true, true});
        instanceVector.push_back({"testid3", "1.2.3.6", "dnsname3", CGOpt::AWSTools::running, true, true, false});

        std::vector<std::string> ipAddresses;

        std::transform(instanceVector.begin(),
                       instanceVector.end(),
                       std::back_inserter(ipAddresses),
                       [](CGOpt::AWSTools::AWSInstance i) {return i.publicIp;} );

        std::string messageQueueIp = instanceVector[1].publicIp;

        ansibleTools.writeHostsFile(instanceVector);
        assertFile(hostsFilePath, ipAddresses, messageQueueIp);
    }

    SECTION("The hosts file is written correctly when separate messagequeue instance") {
        std::string hostsFilePath = "./hosts";
        CGOpt::AnsibleTools ansibleTools;
        ansibleTools.setHostsFilePath(hostsFilePath);

        std::vector<CGOpt::AWSTools::AWSInstance> instanceVector;
        instanceVector.push_back({"testid4", "1.2.3.7", "dnsname4", CGOpt::AWSTools::running, true, true, false});
        instanceVector.push_back({"testid5", "1.2.3.8", "dnsname5", CGOpt::AWSTools::running, true, true, false});
        instanceVector.push_back({"msgqueue", "1.2.3.9", "dnsname6", CGOpt::AWSTools::running, true, false, true});


        std::vector<std::string> ipAddresses;

        std::transform(instanceVector.begin(),
                       instanceVector.end(),
                       std::back_inserter(ipAddresses),
                       [](CGOpt::AWSTools::AWSInstance i) {return i.publicIp;} );

        std::string messageQueueIp = instanceVector[2].publicIp;

        ansibleTools.writeHostsFile(instanceVector);

        ipAddresses.erase(ipAddresses.end()-1);
        assertFile(hostsFilePath, ipAddresses, messageQueueIp);
    }
}
