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
    static std::string runCmd(std::string const &cmd) {
        return runCmd(cmd, redi::pstream::pstdout);
    }

    static std::string runCmdGetCerr(std::string const &cmd) {
        return runCmd(cmd, redi::pstream::pstderr);
    }

    static std::string runCmd(std::string const &cmd, int &retCode) {
        return runCmd(cmd, retCode, redi::pstream::pstdout);
    }

    static std::string runCmdGetCerr(std::string const &cmd, int &retCode) {
        return runCmd(cmd, retCode, redi::pstreams::pstderr);
    }

private:
    static std::string runCmd(std::string const &cmd, const redi::pstream::pmode stream) {
        redi::ipstream proc(cmd, stream);

        std::string output(pstrm_iter(proc.rdbuf()), pstrm_iter());

        return trim(output);
    }

    static std::string runCmd(std::string const &cmd, int &retCode, const redi::pstream::pmode stream) {
        redi::ipstream proc(cmd, stream);

        std::string output(pstrm_iter(proc.rdbuf()), pstrm_iter());

        proc.close();
        if (proc.rdbuf()->exited()) {
            int encodedRetCode = proc.rdbuf()->status();
            retCode = WEXITSTATUS(encodedRetCode);
        }

        return trim(output);
    }
};


