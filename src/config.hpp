#include <yaml-cpp/yaml.h>
#include <istream>
#include <chrono>

class Config // Standard way of defining the class
{
public:
	Config();
	~Config();
	Config& operator=(const Config&);
	Config(const Config&);
	void parsePath(std::string path);
	void addInstance(RemoteInstance ri);
	void removeInstance(int i);
	void showInstances();
private:
	size_t someField;
	std::string awsAccessKeyId;
	std::string awsAccessKeySecret;
	std::vector<RemoteInstance> remoteInstances;
};

class RemoteInstance {
public:
	RemoteInstance();
	RemoteInstance(const YAML::Node& node);
	RemoteInstance(const RemoteInstance&);
	~RemoteInstance();

	enum InstanceType {MSGQUEUE, GPUWORKER};

	RemoteInstance& operator=(const RemoteInstance&);
	const std::string& getIp() const {
		return (ip);
	}

	void setIp(const std::string& ip) {
		this->ip = ip;
	}

	int getPort() const {
		return (port);
	}

	void setPort(int port) {
		this->port = port;
	}

	long getId() const {
		return (id);
	}

	void setId(long id) {
		this->id = id;
	}
private:
	long id;
	std::string ip;
	int port;
};

Config::Config(){
	someField = 0;
	awsAccessKeyId = "";
	awsAccessKeySecret = "";
	remoteInstances.clear();
}

void parsePath(std::string path){
	try {
	    std::ifstream fin(path);
	    YAML::Parser parser(fin);
	    YAML::Node doc;
	    parser.GetNextDocument(doc);
	    // do stuff
	} catch(YAML::ParserException& e) {
	    std::cout << e.what() << "\n";
	}
}

Config::addInstance(RemoteInstance & ri){
	ri.setId(this->remoteInstances.size());
	this->remoteInstances.push_back(ri);
}

Config::showInstances(){
	for_each( this->remoteInstances.begin(), this->remoteInstances.end(), [] (RemoteInstance inst)
			{std::cout << inst.getId() <<"= "<<inst.getIp()<<":"<<inst.getPort();}
	);
}
