//! Brief description.

//! Detailed description 
//! starts here.
#include <iostream>
#include <thread>
#include <tclap/CmdLine.h>
#include <string>
#include "Config.h"
#include "AWS/AWSTools.h"
#include "Manager/CSAOptManager.h"
#include "helpers.h"
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <termios.h>
#include <unistd.h>
#include "InteractiveShell.h"

volatile sig_atomic_t interrupted = 0;

void handleSigInt(int sig) { // can be called asynchronously
    interrupted = 1; // set flag
    std::cout << "Caught " << strsignal(sig) << ", Exiting." << std::endl;

    exit(0);
}

static volatile bool debug = false;

void atExitHandler() {
}


void enterInteractiveLoop(CSAOpt::CSAOptManager &manager) {
    CSAOpt::InteractiveShell shell(manager);
    shell.enter();
}


int main(int argc, const char *const *argv) {
    using namespace CSAOpt;
    signal(SIGINT, handleSigInt);
    const int registeringFailed = std::atexit(atExitHandler);

    if (registeringFailed) {
        std::cerr << "Failed to register at_exit handler. Exiting";
        exit(1);
    }

    try {
        TCLAP::CmdLine cmd("CSAOpt", ' ', "0.0.1");

        TCLAP::ValueArg<std::string> configArg("c", "config", "Config file (JSON)",
                                               true, "config.json", "string");
        cmd.add(configArg);
        TCLAP::SwitchArg verboseSwitch("v", "verbose", "Print verbose output",
                                       cmd, false); //no need to add to cmd, as it is done internally.

        TCLAP::SwitchArg qietSwitch("q", "qiet", "No console output",
                                    cmd, false); //no need to add to cmd, as it is done internally.

        TCLAP::SwitchArg interactiveSwitch("i", "interactive", "Interactive mode",
                                           cmd, false); //no need to add to cmd, as it is done internally.

        TCLAP::SwitchArg debugSwitch("d", "debug", "Extra debug statements",
                                           cmd, false); //no need to add to cmd, as it is done internally.

        // Parse the argv array.
        cmd.parse(argc, argv);

        // Get the value parsed by each arg.
        std::string configPath = configArg.getValue();
        bool verboseOutput = verboseSwitch.getValue();
        bool interactiveMode = interactiveSwitch.getValue();
        debug = debugSwitch.getValue();

        Config::parse(configPath);

        std::string loggerName{Config::loggerName()};
        std::vector<spdlog::sink_ptr> sinks;
        if (!qietSwitch.getValue()) {
            auto console = std::make_shared<spdlog::sinks::stdout_sink_mt>();
            sinks.push_back(std::make_shared<spdlog::sinks::ansicolor_sink>(console));
        }
        if (Config::fileLogging()) {
            sinks.push_back(
                    std::make_shared<spdlog::sinks::rotating_file_sink_mt>("csaopt", "log", 1024 * 1024 * 5, 10));
        }
        auto logger = std::make_shared<spdlog::logger>(loggerName, begin(sinks), end(sinks));
        spdlog::register_logger(logger);

        if (CSAOpt::Config::verboseLogging() || verboseSwitch.getValue()) {
            logger->set_level(spdlog::level::trace);
        }

        CSAOptManager &manager = CSAOptManager::getInstance();

        if (interactiveMode) {
            enterInteractiveLoop(manager);
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
