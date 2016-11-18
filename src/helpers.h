//
// Created by dotdi on 15.11.16.
//

#pragma once

#include <cstdarg>
#include <sys/stat.h>
#include <errno.h>
#include <wordexp.h>

static inline std::string getFilenameFromPath(std::string const &path) {
    return path.substr(path.find_last_of("/\\") + 1);
}

static inline std::string removeFileExtension(std::string const &filename) {
    size_t idx = filename.find_last_of('.');
    return idx > 0 && idx != filename.npos ? filename.substr(0, idx) : filename;
}

static inline std::string getFilenameWithoutExtension(std::string const &path) {
    return removeFileExtension(getFilenameFromPath(path));
}

static inline std::string trim(std::string const &s) {
    auto whitespaceFront = std::find_if_not(s.begin(), s.end(), [](int c) { return std::isspace(c); });
    return std::string(whitespaceFront,
                       std::find_if_not(s.rbegin(), std::string::const_reverse_iterator(whitespaceFront),
                                        [](int c) { return std::isspace(c); }).base());
}

static inline bool file_exists(std::string const &name) {
    struct stat buffer;
    return (stat(name.c_str(), &buffer) == 0);
}

static inline std::string relativePathToAbsolute(std::string const &path) {
    wordexp_t exp_result;
    wordexp(path.c_str(), &exp_result, 0);

    if (exp_result.we_wordc > 0) {
        std::string expandedPath = exp_result.we_wordv[0];

        char *real_path = realpath(expandedPath.c_str(), NULL);
        if(real_path == nullptr){
            return expandedPath;
        }
        std::string filename = std::string{real_path};
        free(real_path);
        return filename;
    }
    return "";
}
