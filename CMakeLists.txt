cmake_minimum_required(VERSION 3.3)
project(csaopt)

set (PROJECT_SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR})

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++1y")
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_CURRENT_SOURCE_DIR}/../CMakeModules) # main (top) cmake dir
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_CURRENT_SOURCE_DIR}/CMakeModules) # project specific cmake dir

include(LibFindMacros)

set(AWS_CPP_BASE /usr/local/Cellar/aws-sdk-cpp/0.12.11/) #MACOS
set(AWS_CPP_BASE_LINUX /usr/local/include/aws/core)
set(AWS_LIB_BASE /usr/local/lib/)

# Include dir
find_path(AWS_SDK_CPP_INCLUDE_DIR
        NAMES Aws.h
        PATHS ${AWS_CPP_BASE} ${AWS_CPP_BASE})

find_library(AWS_SDK_CPP_CORE_LIBRARY
        NAMES libaws-cpp-sdk-core
        PATHS ${AWS_LIB_BASE} ${AWS_CPP_BASE} )

find_library(AWS_SDK_CPP_EC2_LIBRARY
        NAMES libaws-cpp-sdk-ec2
        PATHS ${AWS_LIB_BASE} ${AWS_CPP_BASE} )

set(THREADS_PREFER_PTHREAD_FLAG ON)

find_package(LibUUID REQUIRED)
find_package(Threads REQUIRED)
find_package(Libedit REQUIRED)
find_package(model)

add_subdirectory(model)

include_directories(
#        model
        ${model_INCLUDE_DIR}
        ${model_INCL_DIRS}
        ${Libedit_INCLUDE_DIR}
        ${PROJECT_SOURCE_DIR}/include
        ${PROJECT_BINARY_DIR}/include   # add the binary tree to the search path so that we will find Version.h
)

set(SOURCE_FILES
        src/Config.h
        src/Config.cpp
        src/helpers.h
        src/main.cpp
        src/SysTools.h
        src/AnsibleTools.cpp
        src/AnsibleTools.h
        src/AWS/AWSTools.h
        src/AWS/AWSTools.cpp
        src/Manager/CSAOptManager.h
        src/Manager/CSAOptManager.cpp
        src/OptimizationJob.h
        src/OptimizationJob.cpp
        src/MessageQueueClient.cpp
        src/MessageQueueClient.h
        src/AWS/CSAOptInstance.cpp
        src/AWS/CSAOptInstance.h
        src/AWS/Utils.h
        src/InteractiveShell.cpp
        src/InteractiveShell.h
        src/Manager/ModelValidator.h src/Manager/ModelBuilder.h src/Manager/ModelBuilder.cpp src/Manager/ManagedModel.h)


add_executable(csaopt ${SOURCE_FILES})
add_definitions( -DCSAOPT_MODEL_PATH="${CMAKE_CURRENT_SOURCE_DIR}/model")

set(AWS_INCLUDES aws-cpp-sdk-core aws-cpp-sdk-ec2 Threads::Threads)
target_link_libraries(csaopt model ${AWS_INCLUDES} uuid curses edit)

enable_testing()

add_executable(SysToolsTest test/SysToolsTest.cpp src/SysTools.h)
add_test(NAME SysToolsTest COMMAND SysToolsTest)

add_executable(ConfigTest test/ConfigTest.cpp src/Config.h src/Config.cpp)
add_test(NAME ConfigTest COMMAND ConfigTest)

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


#MESSAGE(WARNING "       model headers=${model_HEADERS} \n
#        model include=${model_INCLUDE_DIRS}")
