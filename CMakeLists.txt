cmake_minimum_required (VERSION 3.9)

project (kilosim
  VERSION 0.4.1
  DESCRIPTION "TODO"
  LANGUAGES C CXX
)

set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake" ${CMAKE_MODULE_PATH})

find_package(HDF5 COMPONENTS CXX HL REQUIRED)
find_package(Sanitizers)
find_package(Doxygen)
find_package(Python3 3.8 REQUIRED COMPONENTS Interpreter NumPy REQUIRED)
find_package(PythonInterp REQUIRED)
find_package(PythonLibs REQUIRED)
find_package(SFML 2.5 COMPONENTS graphics QUIET)
if (NOT SFML_FOUND)
  find_package(SFMLold REQUIRED)
endif()

find_package(OpenMP)



add_library(kilosim
  src/ConfigParser.cpp
  src/LightPattern.cpp
  src/Logger.cpp
  src/Robot.cpp
  src/Viewer.cpp
  src/World.cpp
  src/random.cpp
)

include_directories(${PYTHON_INCLUDE_DIRS})

target_include_directories(kilosim
PUBLIC
  api
  submodules
  ${HDF5_INCLUDE_DIRS}
)

target_link_libraries(kilosim
PUBLIC
  ${HDF5_LIBRARIES}
  ${HDF5_CXX_HL_LIBRARIES}
  ${HDF5_CXX_LIBRARIES}
  ${PYTHON_LIBRARIES} 
  Python3::NumPy
  OpenMP::OpenMP_CXX
  sfml-graphics
  sfml-window
  sfml-system
)

target_compile_options(kilosim
PRIVATE
  -g
  -march=native
  -ffast-math
  -Wall
  -Wextra
)

target_compile_features(kilosim PRIVATE cxx_std_11)

install(TARGETS kilosim ARCHIVE DESTINATION lib)

if (DOXYGEN_FOUND)
  add_custom_target(
    docs
    COMMAND ${DOXYGEN_EXECUTABLE} Doxyfile
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Generating API documentation with Doxygen"
    VERBATIM
  )
else(DOXYGEN_FOUND)
  message("Doxygen needs to be installed to generate the doxygen documentation")
endif(DOXYGEN_FOUND)



add_executable(dynamic_bayesBots dynamicEnvironments/main.cpp)

target_include_directories(dynamic_bayesBots PRIVATE dynamicEnvironments)
target_link_libraries(dynamic_bayesBots PUBLIC kilosim)
target_compile_options(dynamic_bayesBots PRIVATE -g -march=native -Wall -Wextra)
target_compile_features(dynamic_bayesBots PRIVATE cxx_std_11)
install(TARGETS dynamic_bayesBots RUNTIME DESTINATION bin OPTIONAL)
