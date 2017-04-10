//
// Created by dotdi on 09.11.16.
//

#pragma once

#include <random>
#include "CSAOptInstance.h"


namespace CSAOpt {
    const static char charset[] =
            "0123456789"
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    "abcdefghijklmnopqrstuvwxyz";

    std::string randomString(size_t length) {
        auto randchar = []() -> char {
            std::random_device rd;
            std::default_random_engine rng(rd());
            std::uniform_int_distribution<> dist(0, sizeof(charset) / sizeof(*charset) - 2);

            return charset[dist(rng)];
        };
        std::string str(length, 0);
        std::generate_n(str.begin(), length, randchar);
        return str;
    }

    std::string getHomeDir() {
        const char *homeDir = std::getenv("HOME");

        if (!homeDir) {
            struct passwd *pwd = getpwuid(getuid());
            if (pwd) {
                homeDir = pwd->pw_dir;
            }
        }
        return std::string(homeDir);
    }

    inline CSAOptInstance::InstanceState mapState(const Aws::EC2::Model::InstanceState &ec2State) {
        return static_cast<CSAOptInstance::InstanceState>(ec2State.GetCode());
    }


    inline CSAOptInstance mapEC2Instance(const Aws::EC2::Model::Instance ec2Instance) {
        CSAOptInstance inst;
        inst.id = ec2Instance.GetInstanceId();
        inst.state = mapState(ec2Instance.GetState());
        return inst;
    }

     inline Aws::EC2::Model::InstanceType mapType(std::string type) {
        if(type == "m3.medium") {
            return Aws::EC2::Model::InstanceType::m3_medium;
        } else if (type == "t2.micro") {
            return Aws::EC2::Model::InstanceType::t2_micro;
        } else if (type == "g2.2xlarge") {
            return  Aws::EC2::Model::InstanceType::g2_2xlarge;
        } else {
            return Aws::EC2::Model::InstanceType::t2_small;
        }
    }

}
