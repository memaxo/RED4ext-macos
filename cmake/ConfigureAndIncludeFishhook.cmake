add_library(fishhook STATIC)
set_target_properties(fishhook PROPERTIES FOLDER "Dependencies")

set(FISHHOOK_SRC_DIR "${PROJECT_SOURCE_DIR}/deps/fishhook")
target_include_directories(fishhook PUBLIC ${FISHHOOK_SRC_DIR})
target_sources(fishhook PRIVATE 
    ${FISHHOOK_SRC_DIR}/fishhook.h
    ${FISHHOOK_SRC_DIR}/fishhook.c
)
