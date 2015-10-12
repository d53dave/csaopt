#pragma once

#include <istream>
#include <chrono>

namespace CGOpt{
    class Config {
    public:
        Config();
        ~Config();
        Config& operator=(const Config&);
        Config(const Config&);
        Config parsePath(std::string path);

        static bool verboseLogging(){ return true; }
        static bool fileLogging(){ return strncmp(loggerName(), "dailyLogger", 100) == 0; }
        static const char *loggerName(){ return loggerNameStr; }
        static std::string hostFilePath(){ return "./ansible/hosts";}


        enum logLevel {info, warning, error, critical, debug};
    private:
        static bool verbose;
        static constexpr const char* loggerNameStr = "console";
    };
}




