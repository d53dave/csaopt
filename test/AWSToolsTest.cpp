//
// Created by David Sere on 01/10/15.
//

#include "TestConfig.h"
#include "../src/AWSTools.h"

TEST_CASE("AWSTools", "[LOL]"){
    SECTION("Testing"){
        std::string secretKey{"secretKey"};
        std::string accessKey{"accessKey"};
        CGOpt::AWSTools tools(accessKey, secretKey);
        tools.log("LOL");
    }
}
