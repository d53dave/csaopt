//! Brief description.

//! Detailed description 
//! starts here.
#include <iostream>
#include <thread>
#include <tclap/CmdLine.h>
#include <string>
#include "config.hpp"
#include "AWS/AWSTools.h"

int main(int argc, const char *const *argv) {

//    CGOpt::OptimizationJob job;
//    job.optimization = std::make_shared<UserDefinedOptimization>();


    try {
        TCLAP::CmdLine cmd("CSAOpt", ' ', "0.1");

        TCLAP::ValueArg<std::string> configArg("c", "config", "Config file (JSON)",
                                               true, "config.json", "string");
        cmd.add(configArg);
        TCLAP::SwitchArg verboseSwitch("v", "verbose", "Print verbose output",
                                       cmd, false); //no need to add to cmd, as it is done internally.

        TCLAP::SwitchArg interactiveSwitch("i", "interactive", "Interactive mode",
                                           cmd, false); //no need to add to cmd, as it is done internally.

        // Parse the argv array.
        cmd.parse(argc, argv);

        // Get the value parsed by each arg.
        std::string configPath = configArg.getValue();
        bool verboseOutput = verboseSwitch.getValue();
        bool interactiveMode = interactiveSwitch.getValue();

        if (interactiveMode) {
            std::cout << "Startup in interactive mode" << std::endl;
        } else {
            std::cout << "Startup in non-interactive line mode" << std::endl;
        }

        std::cout << "Bye!" << std::endl;

    } catch (TCLAP::ArgException &e) {
        std::cerr << "error: " << e.error() << " for arg " << e.argId()
        << std::endl;
        return (1);
    }
    return (0);
}
