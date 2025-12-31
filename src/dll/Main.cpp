#include "App.hpp"
#include "Image.hpp"
#include "Utils.hpp"
#include "Platform.hpp"

#ifdef RED4EXT_PLATFORM_MACOS

__attribute__((constructor))
static void RED4extInit()
{
    try
    {
        const auto image = Image::Get();
        if (!image->IsCyberpunk())
        {
            return;
        }

        App::Construct();
        
        // On macOS, we can't hook the entry point like on Windows,
        // so we call Startup() directly after Construct().
        // This is safe because we're loaded via DYLD_INSERT_LIBRARIES
        // before the main binary starts.
        auto app = App::Get();
        if (app)
        {
            app->Startup();
        }
    }
    catch (const std::exception& e)
    {
        SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An exception occured while loading RED4ext.\n\n{}",
                                            Utils::Widen(e.what()));
    }
    catch (...)
    {
        SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An unknown exception occured while loading RED4ext.");
    }
}

__attribute__((destructor))
static void RED4extShutdown()
{
    try
    {
        const auto image = Image::Get();
        if (!image->IsCyberpunk())
        {
            return;
        }

        // Call Shutdown() before Destruct() on macOS
        auto app = App::Get();
        if (app)
        {
            app->Shutdown();
        }

        App::Destruct();
    }
    catch (const std::exception& e)
    {
        SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An exception occured while unloading RED4ext.\n\n{}",
                                            Utils::Widen(e.what()));
    }
    catch (...)
    {
        SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An unknown exception occured while unloading RED4ext.");
    }
}

#else

BOOL APIENTRY DllMain(HMODULE aModule, DWORD aReason, LPVOID aReserved)
{
    RED4EXT_UNUSED_PARAMETER(aReserved);

    switch (aReason)
    {
    case DLL_PROCESS_ATTACH:
    {
        DisableThreadLibraryCalls(aModule);

        try
        {
            const auto image = Image::Get();
            if (!image->IsCyberpunk())
            {
                break;
            }

            App::Construct();
        }
        catch (const std::exception& e)
        {
            SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An exception occured while loading RED4ext.\n\n{}",
                                                Utils::Widen(e.what()));
        }
        catch (...)
        {
            SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An unknown exception occured while loading RED4ext.");
        }

        break;
    }
    case DLL_PROCESS_DETACH:
    {
        try
        {
            const auto image = Image::Get();
            if (!image->IsCyberpunk())
            {
                break;
            }

            App::Destruct();
        }
        catch (const std::exception& e)
        {
            SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An exception occured while unloading RED4ext.\n\n{}",
                                                Utils::Widen(e.what()));
        }
        catch (...)
        {
            SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An unknown exception occured while unloading RED4ext.");
        }

        break;
    }
    }

    return TRUE;
}

#endif
