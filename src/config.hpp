#include <yaml-cpp/yaml.h>
#include <istream>

class Config // Standard way of defining the class
{
public:
	Config();
	~Config();
	void operator>> (const YAML::Node& node, Config& config);
	void addInstance(RemoteInstance ri);
	void removeInstance(int i);
private:
	size_t someField;
	std::string awsAccessKeyId;
	std::string awsAccessKeySecret;
	std::vector<RemoteInstance> remoteInstances;
};

class RemoteInstance {
public:
	RemoteInstance();
	RemoteInstance(const std::string& ip, int port);
	~RemoteInstance();
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

	enum InstanceType {

	};
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

Config::operator>> (const YAML::Node& node, Config& config){

}

Config::addInstance(RemoteInstance & ri){
	ri.setId(this->remoteInstances.size());
	this->remoteInstances.push_back(ri);
}
