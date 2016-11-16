//
// Created by dotdi on 16.11.16.
//

#include <histedit.h>
#include "InteractiveShell.h"
#include "helpers.h"
#include "Config.h"

namespace CSAOpt {
    static char *prompt(EditLine *el __attribute__((__unused__))) {
        static char a[] = ">> ";

        return a;
    }

    InteractiveShell::InteractiveShell(CSAOpt::CSAOptManager &_manager) : manager(_manager) {

    };

    void InteractiveShell::enter() {

        /* This holds all the state for our line editor */
        EditLine *el;

        /* This holds the info for our history */
        History *hist;

        /* Temp variables */
        int count;
        const char *line;
        HistEvent ev;

        /* Initialize the EditLine state to use our prompt function and
        emacs style editing. */

        el = el_init("csaopt", stdin, stdout, stderr);
        el_set(el, EL_PROMPT, &prompt);
        el_set(el, EL_EDITOR, "emacs");

        /* Initialize the history */
        hist = history_init();
        if (hist == 0) {
            fprintf(stderr, "history could not be initialized\n");
            return;
        }

        /* Set the size of the history */
        history(hist, &ev, H_SETSIZE, 800);
        history(hist, &ev, H_LOAD, Config::getInteractiveHistoryPath().c_str());

        /* This sets up the call back functions for history functionality */
        el_set(el, EL_HIST, history, hist);

        while (!this->aborted) {
            /* count is the number of characters read.
               line is a const char* of our command line with the tailing \n */
            line = el_gets(el, &count);

            /* In order to use our history we have to explicitly add commands
            to the history */
            if (count > 0) {
                history(hist, &ev, H_ENTER, line);

                std::vector<std::string> args;

                std::string token;
                std::istringstream ss(trim(line));

                while (std::getline(ss, token, ' ')) {
                    args.push_back(trim(token));
                }

                this->manager.handleInteractiveCommand(args[0], args);
            }
        }

        history(hist, &ev, H_SAVE, Config::getInteractiveHistoryPath().c_str());


        /* Clean up our memory */
        history_end(hist);
        el_end(el);
    }

    void InteractiveShell::abort() {
        this->aborted = true;
    }
}