//! Brief description.

//! Detailed description 
//! starts here.
#include <iostream>
#include "tclap/CmdLine.h"
#include <thread>
#include <string>
#include "config.hpp"

int main(int argc, char** argv) {
	try {
		TCLAP::CmdLine cmd("CGOPT!!", ' ', "0.1");

		TCLAP::ValueArg<std::string> configArg("c", "config", "Config file (YAML)",
				true, "config.yml", "string");
		cmd.add(configArg);
		TCLAP::SwitchArg verboseSwitch("v", "verbose", "Print verbose output",
				cmd, false); //no need to add to cmd, as it is done internally.

		// Parse the argv array.
		cmd.parse(argc, argv);

		// Get the value parsed by each arg.
		std::string configPath = configArg.getValue();
		bool verboseOutput = verboseSwitch.getValue();

		// Do what you intend.
		if (verboseOutput) {
			std::cout << "VERBOSE Startup!!! This is very verbose." << std::endl;
			std::cout << "Loading config file from "<< configPath << std::endl;
			try {
			    std::ifstream fin("test.yaml");
			    YAML::Parser parser(fin);
			    YAML::Node doc;
			    parser.GetNextDocument(doc);
			    for(unsigned i=0;i<doc.size();i++) {
			          Monster monster;
			          doc[i] >> monster;
			          std::cout << monster.name << "\n";
			       }
			} catch(YAML::ParserException& e) {
			    std::cout << e.what() << "\n";
			}
		} else {
			std::cout << "Startup!" << std::endl;
		}


	} catch (TCLAP::ArgException &e){
		std::cerr << "error: " << e.error() << " for arg " << e.argId()
				<< std::endl;
		return (1);
	}
	return (0);
}
