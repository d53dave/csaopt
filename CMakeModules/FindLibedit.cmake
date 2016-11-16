include(LibFindMacros)

# Use pkg-config to get hints about paths
libfind_pkg_check_modules(Libedit_PKGCONF libedit)

# Include dir
find_path(LIBEDIT_INCLUDE_DIR
        NAMES histedit.h
        PATHS ${Libedit_PKGCONF_INCLUDE_DIRS})

# Finally the library itself
find_library(LIBEDIT_LIBRARIES
        NAMES edit
        PATHS ${Libedit_PKGCONF_INCLUDE_DIRS})

# Set the include dir variables and the libraries and let libfind_process do the rest.
# NOTE: Singular variables for this library, plural for libraries this this lib depends on.
set(Libedit_PROCESS_INCLUDES Libedit_INCLUDE_DIR )
set(Libedit_PROCESS_LIBS Libedit_LIBRARY )
libfind_process(Libedit)