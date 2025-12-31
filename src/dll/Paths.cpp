#include "Paths.hpp"
#include "Platform.hpp"
#include "Utils.hpp"

Paths::Paths()
{
    m_exe = Platform::GetModuleFileName();
    if (m_exe.empty())
    {
        SHOW_LAST_ERROR_MESSAGE_AND_EXIT_FILE_LINE(L"Could not get game's file name.");
        return;
    }

#ifdef RED4EXT_PLATFORM_MACOS
    m_root = m_exe
                 .parent_path()  // Resolve to "MacOS" directory.
                 .parent_path()  // Resolve to "Contents" directory.
                 .parent_path()  // Resolve to "Cyberpunk2077.app" directory.
                 .parent_path(); // Resolve to game's root directory.
#else
    m_root = m_exe
                 .parent_path()  // Resolve to "x64" directory.
                 .parent_path()  // Resolve to "bin" directory.
                 .parent_path(); // Resolve to game's root directory.
#endif
}

std::filesystem::path Paths::GetRootDir() const
{
    return m_root;
}

std::filesystem::path Paths::GetX64Dir() const
{
#ifdef RED4EXT_PLATFORM_MACOS
    // On macOS the game bundle layout doesn't include a Windows-style `<game_root>/bin/x64`.
    // Keep RED4ext assets (addresses/symbol mappings, etc.) under `<game_root>/red4ext/bin/x64`.
    return GetRED4extDir() / L"bin" / L"x64";
#else
    return GetRootDir() / L"bin" / L"x64";
#endif
}

std::filesystem::path Paths::GetExe() const
{
    return m_exe;
}

std::filesystem::path Paths::GetRED4extDir() const
{
    return GetRootDir() / L"red4ext";
}

std::filesystem::path Paths::GetLogsDir() const
{
    return GetRED4extDir() / L"logs";
}

std::filesystem::path Paths::GetPluginsDir() const
{
    return GetRED4extDir() / L"plugins";
}

std::filesystem::path Paths::GetRedscriptPathsFile() const
{
    return GetRED4extDir() / L"redscript_paths.txt";
}

std::filesystem::path Paths::GetR6Scripts() const
{
    return GetRootDir() / L"r6" / L"scripts";
}

std::filesystem::path Paths::GetDefaultScriptsBlob() const
{
    return GetRootDir() / L"r6" / L"cache" / "final.redscripts";
}

std::filesystem::path Paths::GetR6CacheModded() const
{
    return GetRootDir() / L"r6" / L"cache" / L"modded";
}

std::filesystem::path Paths::GetR6Dir() const
{
    return GetRootDir() / L"r6";
}

const std::filesystem::path Paths::GetConfigFile() const
{
    return GetRED4extDir() / L"config.ini";
}
