//
// Created by dotdi on 15.11.16.
//

#pragma once

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

static inline std::string string_format(const std::string fmt_str, ...) {
    int final_n, n = ((int) fmt_str.size()) * 2; /* Reserve two times as much as the length of the fmt_str */
    std::string str;
    std::unique_ptr<char[]> formatted;
    va_list ap;
    while (1) {
        formatted.reset(new char[n]); /* Wrap the plain char array into the unique_ptr */
        strcpy(&formatted[0], fmt_str.c_str());
        va_start(ap, fmt_str);
        final_n = vsnprintf(&formatted[0], n, fmt_str.c_str(), ap);
        va_end(ap);
        if (final_n < 0 || final_n >= n)
            n += abs(final_n - n + 1);
        else
            break;
    }
    return std::string(formatted.get());
}