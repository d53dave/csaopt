//
// Created by David Sere on 01/10/15.
//

#include "TestConfig.h"
#include "../src/OptimizationJob.h"
#include "Testclasses/UserDefinedTarget.h"
#include "Testclasses/UserDefinedOptimization.h"

TEST_CASE("OptimizationJobTest", "[OptJob]"){

    CSAOpt::OptimizationJob optJob;
    optJob.target = std::make_shared<UserDefinedTarget>();
    optJob.optimization = std::make_shared<UserDefinedOptimization>();
    SECTION("Classes and files should be detected"){
        std::cout << optJob.getTargetClassFile() <<std::endl;
        std::cout << optJob.getOptClassFile() << std::endl;
        std::cout << optJob.optimization.get()->getFileName();
        REQUIRE(true);
    }

}