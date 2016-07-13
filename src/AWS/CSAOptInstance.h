//
// Created by David Sere on 13/07/16.
//

#pragma once

#include <string>

namespace CSAOpt {
    class CSAOptInstance {
    public:
        std::string id;
        std::string publicIp;
        std::string publicDNSname;
        InstanceState state;
        bool isWorker;
        bool isMessageQueue;

        enum class InstanceState {
            pending = 0, running = 16, shutting_down = 32, terminated = 48, stopping = 64, stopped = 80
        };
    };
}

