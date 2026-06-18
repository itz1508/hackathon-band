cmake_minimum_required(VERSION 3.20)
project(AgentSkillsMVP)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Qt6
find_package(Qt6 COMPONENTS Core Gui Qml Quick REQUIRED)

# Find Python
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Set automoc, autorcc, autouic
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Source files
set(SOURCES
    src/main.cpp
    src/backend.h
    src/backend.cpp
)

set(QML_FILES
    frontend/main.qml
)

# Create executable
add_executable(agent-skills-mvp ${SOURCES} ${QML_FILES})

# Link Qt libraries
target_link_libraries(agent-skills-mvp
    Qt6::Core
    Qt6::Gui
    Qt6::Qml
    Qt6::Quick
    Python3::Python
)

# Include Python headers
target_include_directories(agent-skills-mvp PRIVATE ${Python3_INCLUDE_DIRS})

# Set output directory
set_target_properties(agent-skills-mvp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)

# Copy QML files to build directory
add_custom_command(TARGET agent-skills-mvp POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    "${CMAKE_SOURCE_DIR}/frontend"
    "${CMAKE_BINARY_DIR}/bin/frontend"
    COMMENT "Copying QML files..."
)

# Copy Python backend to build directory
add_custom_command(TARGET agent-skills-mvp POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    "${CMAKE_SOURCE_DIR}/backend"
    "${CMAKE_BINARY_DIR}/bin/backend"
    COMMENT "Copying Python backend..."
)

# Installation
install(TARGETS agent-skills-mvp DESTINATION bin)
install(DIRECTORY frontend/ DESTINATION share/agent-skills-mvp/frontend)
install(DIRECTORY backend/ DESTINATION share/agent-skills-mvp/backend)
