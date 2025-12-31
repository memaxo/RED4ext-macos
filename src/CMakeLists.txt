add_subdirectory(dll)

if(WIN32)
  add_subdirectory(loader)
  add_subdirectory(playground)
endif()
