//
// Created by dotdi on 14.11.16.
//
#include "../src/Config.h"
#include "TestConfig.h"

using namespace CSAOpt;

SCENARIO("Config: Default Values") {

}

SCENARIO("Config: Parsing") {
    GIVEN("one key value pair") {
        std::string testconf{
                "logger.name = asda\n"
        };

        char *tmpname = strdup("/tmp/csaopt.configtest.XXXXXX");
        mkstemp(tmpname);
        std::ofstream ofstream(tmpname);
        ofstream << testconf;
        ofstream.close();

        WHEN("Parsing the file") {
            Config::parse(tmpname);

            THEN("The value should be returned correctly") {
                REQUIRE(Config::loggerName() == "asda");
            }
        }
    }
}

