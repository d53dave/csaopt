include(LibFindMacros)

# Use pkg-config to get hints about paths
libfind_pkg_check_modules(UUID_PKGCONF uuid)

# Include dir
find_path(UUID_INCLUDE_DIR
        NAMES uuid.h
        PATHS ${UUID_PKGCONF_INCLUDE_DIRS}
        )

# Finally the library itself
find_library(UUID_LIBRARY
        NAMES uuid
        PATHS ${UUID_PKGCONF_LIBRARY_DIRS}
        )

# Set the include dir variables and the libraries and let libfind_process do the rest.
# NOTE: Singular variables for this library, plural for libraries this this lib depends on.
set(UUID_PROCESS_INCLUDES UUID_INCLUDE_DIR)
set(UUID_PROCESS_LIBS UUID_LIBRARY )
libfind_process(UUID)