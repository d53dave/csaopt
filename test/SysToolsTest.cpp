//
// Created by David Sere on 05/10/15.
//

#import "TestConfig.h"
#import "../src/SysTools.h"

class SysToolsTester : public SysTools{

};

std::string randomString(unsigned int length) {
    static const char alphanum[] =
            "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

    std::string str{""};
    for (int i = 0; i < length; ++i) {
        str += (alphanum[rand() % (sizeof(alphanum) - 1)]);
    }
    return str;
}

TEST_CASE("Systools runCmd return string and return code", "[SysTools]"){

    SysToolsTester tester;

    SECTION("Systools returns the string from running a command"){
        const std::string testString{"Testing this"};
        int returnCode;

        std::string returnString1 = tester.runCmd("echo \""+testString+"\"");
        std::string returnString2 = tester.runCmd("echo \""+testString+"\"", returnCode);

        REQUIRE( returnString1 == testString );
        REQUIRE( returnString2 == testString );
    }

    SECTION("Systools sets return codes accordingly"){
        const std::string happyCommand{"exit 0"};
        const std::string sadCommand{"exit 1"};
        const std::string verySadCommand{"nonexistent"+randomString(10)+" > /dev/null 2>&1"};

        int happyReturnCode = 42;
        int sadReturnCode = 42;
        int evenSadderReturnCode = 42;

        tester.runCmd(happyCommand, happyReturnCode);
        tester.runCmd(sadCommand, sadReturnCode);
        tester.runCmd(verySadCommand, evenSadderReturnCode);

        REQUIRE( happyReturnCode == 0 );
        REQUIRE( sadReturnCode == 1);
        REQUIRE( evenSadderReturnCode == 127);
    }
}



