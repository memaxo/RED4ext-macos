option(RED4EXT_USE_PCH "" ON)
if(APPLE)
  set(RED4EXT_USE_PCH OFF)
  set(RED4EXT_HEADER_ONLY ON CACHE BOOL "" FORCE)
  
  # Point to the local SDK clone for macOS development
  set(RED4EXT_SDK_DIR "/Users/jackmazac/Development/RED4ext.SDK")
  set(RED4EXT_SDK_INCLUDE_DIR "${RED4EXT_SDK_DIR}/include")
  
  add_library(RED4ext.SDK INTERFACE)
  target_include_directories(RED4ext.SDK INTERFACE "${RED4EXT_SDK_INCLUDE_DIR}")
  add_library(RED4ext::SDK ALIAS RED4ext.SDK)
else()
  add_subdirectory(deps/red4ext.sdk)
endif()
set_target_properties(RED4ext.SDK PROPERTIES FOLDER "Dependencies")

mark_as_advanced(
  RED4EXT_BUILD_EXAMPLES
  RED4EXT_HEADER_ONLY
  RED4EXT_USE_PCH
  RED4EXT_INSTALL
)
