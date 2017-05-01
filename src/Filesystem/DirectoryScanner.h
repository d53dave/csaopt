#pragma once

#include <fnmatch.h>
#include <string>
#include <fts.h>
#include <errno.h>

namespace CSAOpt {
    class DirectoryScanner {
    public:
        static std::vector<std::string> findClassWithNameIn(std::string &className, std::string baseFolder) {
            char const * fpaths[] = {
                   baseFolder.c_str(), NULL
            };

            std::set<std::string> lookingForNames;
            lookingForNames.emplace(className + ".hpp");
            lookingForNames.emplace(className + ".h");
            lookingForNames.emplace(className + ".cpp");
            lookingForNames.emplace(className + ".cc");

            return walk(const_cast<char *const *>(fpaths), lookingForNames);
        }

    private:
        static std::vector<std::string> walk(char *const *fpaths, std::set<std::string> names) {
            std::vector<std::string> foundFiles;

            FTS *tree = fts_open(fpaths, FTS_NOCHDIR, 0);
            if (!tree) {
                perror("fts_open");
                return foundFiles;
            }

            FTSENT *node;
            while ((node = fts_read(tree))) {
                if (node->fts_level > 0 && node->fts_name[0] == '.')
                    fts_set(tree, node, FTS_SKIP);
                else if (node->fts_info & FTS_F) {

                    if(names.find(std::string{node->fts_name}) != names.end()){
                        foundFiles.push_back(std::string{node->fts_accpath});
                    }

                    printf("got file named %s at depth %d, "
                                   "accessible via %s from the current directory "
                                   "or via %s from the original starting directory\n",
                           node->fts_name, node->fts_level,
                           node->fts_accpath, node->fts_path);
                }
            }

            //TODO add logging

            if (errno) {
                perror("fts_read");
            }

            if (fts_close(tree)) {
                perror("fts_close");
            }

            return foundFiles;
        }
    };
}