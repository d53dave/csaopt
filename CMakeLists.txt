cmake_minimum_required(VERSION 3.3)
project(csaopt)

set(PROJECT_INCLUDE_DIR ${PROJECT_SOURCE_DIR}/include )
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++1y")
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_SOURCE_DIR}/CMakeModules)

include(LibFindMacros)

set(AWS_CPP_BASE /usr/local/Cellar/aws-sdk-cpp/0.12.11/) #MACOS
set(AWS_CPP_BASE_LINUX /usr/local/include/aws/core/Aws.h)

# Include dir
find_path(AWS_SDK_CPP_INCLUDE_DIR
        NAMES Aws.h
        PATHS ${AWS_CPP_BASE} ${AWS_CPP_BASE_LINUX})

find_library(AWS_SDK_CPP_CORE_LIBRARY
        NAMES libaws-cpp-sdk-core
        PATHS ${AWS_CPP_BASE} ${AWS_CPP_BASE_LINUX})

find_library(AWS_SDK_CPP_EC2_LIBRARY
        NAMES libaws-cpp-sdk-ec2
        PATHS ${AWS_CPP_BASE} ${AWS_CPP_BASE_LINUX})

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

add_subdirectory(model)

include_directories("${PROJECT_INCLUDE_DIR}")

set(SOURCE_FILES
        src/config.hpp
        src/main.cpp
        src/SysTools.h
        src/AnsibleTools.cpp
        src/AnsibleTools.h
        src/AWS/AWSTools.h
        src/AWS/AWSTools.cpp
        src/CGOptManager.h
        src/CGOptManager.cpp
        src/OptimizationJob.h
        src/OptimizationJob.cpp
        src/MessageQueueClient.cpp
        src/MessageQueueClient.h
        src/AWS/CSAOptInstance.cpp
        src/AWS/CSAOptInstance.h
        src/AWS/Utils.h)


add_executable(csaopt ${SOURCE_FILES})

set(AWS_INCLUDES aws-cpp-sdk-core aws-cpp-sdk-ec2 Threads::Threads)

target_link_libraries(csaopt model ${AWS_INCLUDES})

enable_testing()

add_executable(SysToolsTest test/SysToolsTest.cpp src/SysTools.h)
add_test(NAME SysToolsTest COMMAND SysToolsTest)

add_executable(AnsibleToolsTest test/AnsibleToolsTest.cpp src/AnsibleTools.h src/AnsibleTools.cpp)
add_test(NAME AnsibleToolsTest COMMAND AnsibleToolsTest)

add_executable(AWSToolsTest test/AWSToolsTest.cpp src/AWS/AWSTools.h src/AWS/AWSTools.cpp src/SysTools.h)
target_link_libraries(AWSToolsTest model ${AWS_INCLUDES})
add_test(NAME AWSToolsTest COMMAND AwsToolsTest)

file(GLOB TEST_CLASSES "test/TestClasses/UserDefined*.*")

add_executable(OpimizationJobTest test/OptimizationJobTest.cpp src/OptimizationJob.cpp
        src/OptimizationJob.h ${TEST_CLASSES})
target_link_libraries(OpimizationJobTest model aws-cpp-sdk-core aws-cpp-sdk-ec2)
add_test(NAME OpimizationJobTest COMMAND OpimizationJobTest)

#file(GLOB TEST_FILES "test/*Test.cpp")
#
##Run through each source
#foreach(testFile ${TEST_FILES})
#    #Extract the filename without an extension (NAME_WE)
#    get_filename_component(testName ${testFile} NAME_WE)
#
#    #Add compile target
#    add_executable(${testName} ${testFile} ${SOURCE_FILES})
#    target_link_libraries(${testName} model)
#    add_test(NAME ${testName} COMMAND ${testName} )
#endforeach(testFile)

