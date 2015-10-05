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
	void removeInstance(int i);
	void showInstances();
private:
	size_t someField;
	std::string awsAccessKeyId;
	std::string awsAccessKeySecret;
};



