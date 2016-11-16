//
// Created by dotdi on 16.11.16.
//

#pragma once

#include "CSAOptManager.h"

namespace CSAOpt {

    class InteractiveShell {
    public:
        void enter();
        void abort();

        InteractiveShell(CSAOpt::CSAOptManager &_manager);
        ~InteractiveShell() {
            abort();
        };
    private:
        CSAOpt::CSAOptManager &manager;
        bool aborted = false;
    };
}


