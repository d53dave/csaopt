include(LibFindMacros)


# Include dir
find_path(model_INCLUDE_DIR
        NAMES Optimization.h Target.h
        PATHS ${CMAKE_SOURCE_DIR}/model/src
        )

find_library(model_LIBRARY
        NAMES model
        PATHS ${CMAKE_BINARY_DIR}/model
        )


include(FindPackageHandleStandardArgs)


# Set the include dir variables and the libraries and let libfind_process do the rest.
# NOTE: Singular variables for this library, plural for libraries this this lib depends on.
find_package_handle_standard_args(model DEFAULT_MSG
        model_LIBRARY model_INCLUDE_DIR)

mark_as_advanced(model_INCLUDE_DIR model_LIBRARY )

set(model_LIBRARIES ${model_LIBRARY} )
set(model_INCLUDE_DIRS ${model_INCLUDE_DIR} )
