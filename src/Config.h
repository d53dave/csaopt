#pragma once

#include <istream>
#include <chrono>
#include <map>
#include <sstream>
#include <string>
#include <fstream>
#include <spdlog/spdlog.h>
#include "helpers.h"

namespace CSAOpt {
    class Config {
    public:
        static void parse(std::string path) {
            auto logger = spdlog::get(Config::loggerName());
            //TODO: do some validation
            std::ifstream file(path);
            std::string line;
            while (std::getline(file, line)) {
                if (line.find("=") == std::string::npos) {
                    logger->warn("Config::parse: Line '{}' malformed, skipping.", line);
                    continue;
                }
                config[trim(line.substr(0, line.find('=')))] = trim(line.substr(line.find('=') + 1));
            }
        };

        static bool verboseLogging() {
            return config["logger.verbose"] == "true";
        }

        static bool fileLogging() {
            return config["logger.name"] == "file";
        }

        static std::string loggerFileName() {
            return config["logger.filename"];
        }

        static std::string loggerName() {
            return config["logger.name"];
        }

        static std::string hostFilePath() {
            return config["ansible.hosts"];
        }

        static std::string getInteractiveHistoryPath() {
            return config["interactive.histpath"];
        }

        static std::string getAll() {
            std::stringstream ss;
            ss << std::endl;
            for (auto &&kvp : config) {
                ss << kvp.first << " = " << kvp.second << std::endl;
            }
            return ss.str();
        }

        static std::string get(std::string &key) {
            return config[key];
        }

        static std::string get(std::string &&key) {
            return config[key];
        }

    private:
        typedef std::map<std::string, std::string> ConfigMap;

        Config() { };

        ~Config() = default;

        static ConfigMap config;
    };
}




