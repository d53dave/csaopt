cmake_minimum_required(VERSION 3.3)
project(cgopt)

set(PROJECT_INCLUDE_DIR ${PROJECT_SOURCE_DIR}/include )
set(CMAKE_CXX_STANDARD 11) # adds -std=c++11
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(model)

include_directories("${PROJECT_INCLUDE_DIR}")

set(SOURCE_FILES
        src/config.hpp
        src/main.cpp
        src/SysTools.h
        src/AnsibleTools.cpp
        src/AnsibleTools.h
        src/AWSTools.h
        src/AWSTools.cpp
        src/CGOptManager.h
        src/CGOptManager.cpp
        src/OptimizationJob.h
        src/OptimizationJob.cpp
)


add_executable(cgopt ${SOURCE_FILES})

target_link_libraries(cgopt model)

enable_testing()

add_executable(SysToolsTest test/SysToolsTest.cpp src/SysTools.h)
add_test(NAME SysToolsTest COMMAND SysToolsTest)

add_executable(AWSToolsTest test/AWSToolsTest.cpp src/AWSTools.h src/AWSTools.cpp src/SysTools.h)
target_link_libraries(AWSToolsTest model)
add_test(NAME AWSToolsTest COMMAND AwsToolsTest)

file(GLOB TEST_CLASSES "test/TestClasses/*.*")

add_executable(OpimizationJobTest test/OptimizationJobTest.cpp src/OptimizationJob.cpp
        src/OptimizationJob.h ${TEST_CLASSES})
target_link_libraries(OpimizationJobTest model)
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

