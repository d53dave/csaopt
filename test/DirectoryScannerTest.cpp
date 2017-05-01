#include "TestConfig.h"
#include "../src/Filesystem/DirectoryScanner.h"
#include <stdlib.h>

TEST_CASE("DirectoryScannerTest", "[DirScanner]") {

    SECTION("Files should be detected") {
        GIVEN("Class files exist") {
            long now = std::chrono::duration_cast< std::chrono::milliseconds >(
                    std::chrono::system_clock::now().time_since_epoch()
            ).count();

            std::string className{"TestClass"};
            std::string tempFolder{"/tmp/" + std::to_string(now) + "/b/"};
            std::string tempHeader = className + ".cpp";
            std::string tempImplementation = className + ".hpp";

            // TODO: This assumes some form of GNU/Linux, or at least a shell with mkdir
            system(("mkdir -p " + tempFolder).c_str());
            std::ofstream out(tempFolder + tempHeader);
            out << "headercontent";
            out.close();

            std::ofstream out2(tempFolder + tempImplementation);
            out2 << "implcontent";
            out2.close();

            WHEN("Trying to find class") {
                auto paths = CSAOpt::DirectoryScanner::findClassWithNameIn(className, "/tmp/" + std::to_string(now));

                THEN("Result should be correct path") {
                    REQUIRE(paths.size() == 2);
                    REQUIRE(paths.at(0) == tempFolder + tempHeader);
                    REQUIRE(paths.at(1) == tempFolder + tempImplementation);

                }

                system(("rm -r " + tempFolder).c_str());
            }
        };



    }

    SECTION("Non-existing Files should not be detected") {
        GIVEN("Path does not exist") {

        }

        GIVEN("Path exists but files do not") {

        }
    }

}