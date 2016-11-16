//! Brief description.

//! Detailed description 
//! starts here.
#include <iostream>
#include <thread>
#include <tclap/CmdLine.h>
#include <string>
#include "Config.h"
#include "AWS/AWSTools.h"
#include "CSAOptManager.h"
#include "helpers.h"
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <termios.h>
#include <unistd.h>

volatile sig_atomic_t interrupted = 0;
static struct termios oldt, newt;
static int oldf;

void handleSigInt(int sig) { // can be called asynchronously
    interrupted = 1; // set flag
    std::cout << "Caught " << strsignal(sig) << ", Exiting." << std::endl;

    exit(0);
}

static bool debug = false;

void makeRaw() {
//    systemetem ("/bin/stty raw");
    /*tcgetattr gets the parameters of the current terminal
    STDIN_FILENO will tell tcgetattr that it should write the settings
    of stdin to oldt*/
    tcgetattr(STDIN_FILENO, &oldt);
    /*now the settings will be copied*/
    newt = oldt;

    /*ICANON normally takes care that one line at a time will be processed
    that means it will return if it sees a "\n" or an EOF or an EOL*/
    newt.c_lflag &= ~(ICANON | ECHO);

    /*Those new settings will be set to STDIN
    TCSANOW tells tcsetattr to change attributes immediately. */
    tcsetattr(STDIN_FILENO, TCSANOW, &newt);

//    tcgetattr(STDIN_FILENO, &oldt);
//    newt = oldt;
//    newt.c_lflag &= ~(ICANON | ECHO);
//    tcsetattr(STDIN_FILENO, TCSANOW, &newt);
    oldf = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, oldf | O_NONBLOCK);
}

void unmakeRaw() {
//    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
    fcntl(STDIN_FILENO, F_SETFL, oldf);
    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
//    fflush(stdout);
//    system("stty sane; tput rs1;");
}

void atExitHandler() {
//    tcsetattr( STDOUT_FILENO, TCSANOW, &oldtout);
    unmakeRaw();
}

void replaceLine(std::string newline) {
    std::cout << "\33[2K\r" << newline;
}

void enterInteractiveLoop(CSAOpt::CSAOptManager &manager) {
    auto logger = spdlog::get(CSAOpt::Config::loggerName());
    std::string promptmessage = ">> ";
    std::cout << promptmessage;
    size_t historyPos = 0;
    std::vector<std::string> history;

    size_t curStringPos = 0;
    std::string inputString{""};

    const int ctrlC = 3;
    const int ctrlD = 4;
    const int up = 0x26;
    const int down = 0x28;
    const int left = 0x25;
    const int right = 0x27;
    const int back = 127;
    const int enter = 10;

//    std::cout << "\033[?25h";


    makeRaw();
    while (interrupted == 0) {
//        std::cout << "\033[10;20H";
        int c = std::getchar();

        if (c == -1) {
            continue;
        }

//        std::cout << "Got character " << c << std::endl;
        if (c == enter) {
            if (inputString.size() < 1) {
                std::cout << std::endl;
                replaceLine(promptmessage);
                continue;
            }
            std::cout << "Handling return" << std::endl;
            std::vector<std::string> args;

            std::string token;
            std::istringstream ss(inputString);

            std::cout << "Tokenizing" << std::endl;
            while (std::getline(ss, token, ' ')) {
                args.push_back(trim(token));
            }

            std::cout << "Tokeinzed to " << args.size() << " tokens." << std::endl;
            try {
                inputString.clear();
                curStringPos = 0;

                std::cout << std::endl;
                manager.handleInteractiveCommand(trim(args[0]), args);
            } catch (const std::exception &e) {
                std::cerr << "An error occured: " << e.what() << ". Exiting." << std::endl;
                break;
            }
            replaceLine("\r\n" + promptmessage);
            history.push_back(inputString);
            historyPos = history.size() - 1;
        } else if (c == '\033') { // if the first value is esc
            std::cout << "Got \\033" << std::endl;
            getchar();
            c = getchar();
            switch (c) { // the real value
                case 'A':
                    std::cout << "Got UP" << std::endl;
                    // code for arrow up
                    if (historyPos - 1 > -1) {
                        inputString = history.at(historyPos);
                        curStringPos = inputString.size() - 1;
                        replaceLine(promptmessage + inputString);
                        --historyPos;
                    }
                    break;
                case 'B':
                    std::cout << "Got DOWN" << std::endl;
                    if (historyPos - 1 < history.size()) {
                        inputString = history.at(historyPos);
                        curStringPos = inputString.size() - 1;
                        replaceLine(promptmessage + inputString);
                        ++historyPos;
                    }
                    // code for arrow down
                    break;
                case 'D':
                    //std::cout << "Got LEFT" << std::endl;
                    if (curStringPos > 0) {
                        std::cout << "Moving LEFT" << std::endl;
                        std::cout << "\033[1D";
                        --curStringPos;
                    }

                    // code for arrow right
                    break;
                case 'C':
                    //std::cout << "Got RIGHT" << std::endl;
                    if (curStringPos < (inputString.size() - 1)) {
                        std::cout << "Moving RIGHT" << std::endl;
                        std::cout << "\033[1C";
                        ++curStringPos;
                    }
                    // code for arrow left
                    break;
            }
        } else if (c == back) {
//            std::cout << "Got BCKSPC" << std::endl;
            if (curStringPos > 0) {
//                std::cout << "deleting char " << curStringPos << std::endl;
                inputString.erase(curStringPos - 1, 1);
//                std::cout << "input is now " << inputString << std::endl;
                --curStringPos;
                replaceLine(promptmessage + inputString);
            }
        } else if (c == ctrlC) {
            std::cout << "SIGINT" << std::endl;
            raise(SIGINT);
        } else if (c == ctrlD) {
            std::cout << "EOF" << std::endl;
            break;
        } else {
            inputString.insert(curStringPos, std::string{static_cast<wchar_t>(c)});
            ++curStringPos;
            replaceLine(promptmessage + inputString);
        }
    }
    unmakeRaw();
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

        Config::parse(configArg.getValue());

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
