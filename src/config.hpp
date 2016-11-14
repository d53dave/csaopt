#pragma once

#include <istream>
#include <chrono>
#include <map>
#include <sstream>
#include <string>
#include <fstream>
#include <spdlog/spdlog.h>

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

        static std::string getAll() {
            std::stringstream ss;
            for (auto &&kvp : config) {
                ss << kvp.first << "=" << std::endl;
            }
            return ss.str();
        }

    private:
        typedef std::map<std::string, std::string> ConfigMap;

        Config() { };

        ~Config() = default;

        static ConfigMap config;

        static inline std::string trim(const std::string &s) {
            auto whitespaceFront = std::find_if_not(s.begin(), s.end(), [](int c) { return std::isspace(c); });
            return std::string(whitespaceFront,
                               std::find_if_not(s.rbegin(), std::string::const_reverse_iterator(whitespaceFront),
                                                [](int c) { return std::isspace(c); }).base());
        }
    };
}




