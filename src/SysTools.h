//
// Created by David Sere on 28/09/15.
//
#pragma once

#include "pstream/pstream.h"
#include <ios>
#include <cctype>
#include <string>
#include <algorithm>

typedef std::istreambuf_iterator<char> pstrm_iter;

class SysTools {
public:
    std::string runCmd(const std::string cmd) const {
        redi::ipstream proc(cmd);

        std::string output(pstrm_iter(proc.rdbuf()), pstrm_iter());

        return trim(output);
    }

    std::string runCmd(const std::string cmd, int &retCode) const {
        redi::ipstream proc(cmd);

        std::string output(pstrm_iter(proc.rdbuf()), pstrm_iter());

        proc.close();
        if (proc.rdbuf()->exited()){
            int encodedRetCode = proc.rdbuf()->status();
            retCode = WEXITSTATUS(encodedRetCode);
        }

        return trim(output);
    }
private:
    inline std::string trim(const std::string &s) const
    {
        auto wsfront = std::find_if_not(s.begin(),s.end(), [](int c){return std::isspace(c);});
        return std::string(wsfront,
                           std::find_if_not(
                                   s.rbegin(),
                                   std::string::const_reverse_iterator(wsfront),
                                   [](int c){return std::isspace(c);}).base()
        );
    }
};


