//
// Created by David Sere on 01/10/15.
//

#include "TestConfig.h"
#include "../src/AWS/AWSTools.h"

TEST_CASE("AWSTools", "[AWS]"){
    SECTION("AWSTools can be instantiated"){
        std::string secretKey{"secretKey"};
        std::string accessKey{"accessKey"};
        CSAOpt::AWSTools tools(accessKey, secretKey);
    }
#ifdef AWS_TEST_FULL
    SECTION("AWSTools starts the desired count of instances"){
        const char* accessKey = std::getenv("AWS_Access_Key_ID");
        const char* secretKey = std::getenv("AWS_Secret_Access_Key");

        REQUIRE(accessKey);
        REQUIRE(secretKey);

        int instanceCount = 3;

        CSAOpt::AWSTools tools(accessKey, secretKey, CSAOpt::AWSTools::EUWEST1, instanceCount);
//        tools.runSetup();



        REQUIRE(tools.getInstances().size() == instanceCount);
    }

#endif
}
