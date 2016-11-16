//
// Created by David Sere on 28/09/15.
//
#pragma once

#include "helpers.h"
#include <ios>
#include <cctype>
#include <string>
#include <algorithm>
#include <pstream/pstream.h>

typedef std::istreambuf_iterator<char> pstrm_iter;

class SysTools {
public:
    static std::string runCmd(const std::string cmd) {
        redi::ipstream proc(cmd);

        std::string output(pstrm_iter(proc.rdbuf()), pstrm_iter());

        return trim(output);
    }

    static std::string runCmd(const std::string cmd, int &retCode) {
        redi::ipstream proc(cmd);

        std::string output(pstrm_iter(proc.rdbuf()), pstrm_iter());

        proc.close();
        if (proc.rdbuf()->exited()){
            int encodedRetCode = proc.rdbuf()->status();
            retCode = WEXITSTATUS(encodedRetCode);
        }

        return trim(output);
    }
};


