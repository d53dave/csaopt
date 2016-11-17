//
// Created by dotdi on 15.11.16.
//

#pragma once

#include <cstdarg>
#include <sys/stat.h>

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
