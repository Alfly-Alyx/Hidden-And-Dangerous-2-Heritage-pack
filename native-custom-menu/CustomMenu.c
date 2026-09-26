/* H&D2 1.12 native custom-mission menu, loaded by Ultimate ASI Loader.
 * Does not rewrite the game EXE or start a game. Starts the session monitor.
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>

#define EXPORT __declspec(dllexport)
#define WORD_AT(address) (*(unsigned *)(address))

EXPORT unsigned MenuView = 0; /* 0=official, 2=categories, 3..5=custom lists */
EXPORT unsigned MenuSavedVisibility = 0xffffffff;
EXPORT unsigned MenuCustomVisibility = 0;
EXPORT unsigned MenuLastEvent = 0;
EXPORT unsigned MenuLastMaskedEvent = 0;
EXPORT const char MenuControlName[] = "bcampaign02";
EXPORT const char MenuPlayerControlName[] = "bcustom user";
EXPORT const char MenuMultiControlName[] = "bcustom multi";
EXPORT const char MenuExploreControlName[] = "bcustom explore";
EXPORT void *MenuMissionScreen;
EXPORT void *MenuMissionScene;
/* Build-time definitions, NOT live GUI controls. The engine releases them
 * after construction, so copy their routing IDs before the builder returns. */
EXPORT void *MenuCategoryControls[4];
EXPORT unsigned MenuCategoryIds[3];
static LONG initialized;
static char logPath[MAX_PATH];
static unsigned lastDecodedCatalogue = 0xffffffff;
static unsigned lastDecodedRow = 0xffffffff;

extern int GameCount(unsigned catalogue);
extern int GameCountForManager(void *manager, unsigned catalogue);
extern void GameReload(void *screen);
extern void GamePostMenuMessage(const unsigned *message);
extern unsigned GameCurrentScreenId(void);
EXPORT unsigned MenuActivateAction(unsigned action);
EXPORT void HookBuild(void);
EXPORT void HookCustomCallback(void);
EXPORT void HookPlayerCallback(void);
EXPORT void HookMultiCallback(void);
EXPORT void HookExploreCallback(void);
EXPORT void HookMissionBuild(void);
EXPORT void HookAction(void);
EXPORT void HookEventDispatch(void);
EXPORT void HookBackDispatch(void);
EXPORT void HookListBegin(void);
EXPORT void HookListOffset(void);
EXPORT void HookLabelOffset(void);
EXPORT void HookOfficialGroups(void);
EXPORT void HookListNext(void);
EXPORT void HookRowClick(void);
EXPORT void HookRowDecode(void);
EXPORT void HookSelect(void);
EXPORT void HookNativeSingle(void);
EXPORT void HookNativeCarnage(void);
EXPORT void HookCatalogueReset(void);
EXPORT void HookTitle(void);
EXPORT void HookRefreshDone(void);

static void Log(const char *message)
{
    DWORD written;
    HANDLE file = CreateFileA(logPath, FILE_APPEND_DATA,
        FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL, NULL);
    if (file == INVALID_HANDLE_VALUE) return;
    WriteFile(file, message, (DWORD)strlen(message), &written, NULL);
    WriteFile(file, "\r\n", 2, &written, NULL);
    CloseHandle(file);
}

static void StartDiagnostics(void)
{
    char executable[MAX_PATH];
    char gamePath[MAX_PATH];
    char command[MAX_PATH * 2 + 96];
    char line[160];
    char *slash;
    STARTUPINFOA startup;
    PROCESS_INFORMATION process;
    GetModuleFileNameA(NULL, gamePath, sizeof(gamePath));
    slash = strrchr(gamePath, '\\');
    if (!slash) return;
    if ((unsigned)(slash - gamePath) + 1
            + strlen("HD2-Heritage-Diagnostics.exe") >= sizeof(gamePath)) return;
    strcpy(slash + 1, "HD2-Heritage-Diagnostics.exe");
    strcpy(executable, gamePath);
    if (GetFileAttributesA(executable) == INVALID_FILE_ATTRIBUTES) {
        Log("Diagnostic monitor is not installed.");
        return;
    }
    *slash = 0;
    sprintf(command, "\"%s\" --watch-pid %lu \"%s\"",
        executable, (unsigned long)GetCurrentProcessId(), gamePath);
    memset(&startup, 0, sizeof(startup));
    memset(&process, 0, sizeof(process));
    startup.cb = sizeof(startup);
    if (!CreateProcessA(executable, command, NULL, NULL, FALSE,
            CREATE_NO_WINDOW, NULL, gamePath, &startup, &process)) {
        sprintf(line, "Could not start diagnostic monitor; Windows error %lu.",
            (unsigned long)GetLastError());
        Log(line);
        return;
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    Log("Diagnostic monitor started for this game session.");
}

/* Log the catalogue state produced by the actual loader, not a disk scan. */
EXPORT void MenuLogCatalogues(void *pointer)
{
    unsigned manager=(unsigned)pointer, index, count;
    char line[160], directory[MAX_PATH];
    if(!manager) { Log("catalogue-load manager=absent"); return; }
    count=(WORD_AT(manager+12)-WORD_AT(manager+8))/4;
    if (!GetCurrentDirectoryA(sizeof(directory),directory))
        strcpy(directory,"(current directory unavailable)");
    sprintf(line,"catalogue-load count=%u view=%u",count,MenuView);
    Log(line); Log(directory);
    if(count>256) { Log("catalogue-load invalid count"); return; }
    for(index=0;index<count;index++) {
        sprintf(line,"catalogue-loaded index=%u missions=%d",index,
            GameCountForManager(pointer,index));
        Log(line);
    }
}

static unsigned CatalogueCount(void)
{
    unsigned manager = WORD_AT(0x8aea10);
    if (!manager) return 0;
    return (WORD_AT(manager + 12) - WORD_AT(manager + 8)) / 4;
}

/* The stock browser assumes two catalogues. Both flat-list label creation
 * and visibility reuse catalogue 0's size for every later catalogue.
 * All three paths (labels, visibility, clicks) need cumulative offsets.
 */
EXPORT unsigned MenuOffset(unsigned catalogue)
{
    unsigned index, total = 0;
    if (catalogue > CatalogueCount()) return 0xffffffff;
    for (index = 0; index < catalogue; index++) {
        int count = GameCount(index);
        if (count < 0 || count > 255 || total + count > 255) return 0xffffffff;
        total += count;
    }
    return total;
}

/* x86 ABI returns the catalogue in EAX and the local row in EDX. */
EXPORT unsigned long long MenuDecode(unsigned row)
{
    unsigned index, count = CatalogueCount();
    for (index = 0; index < count; index++) {
        int size = GameCount(index);
        if (size < 0) break;
        if (row < (unsigned)size) {
            if (logPath[0] && (index != lastDecodedCatalogue || row != lastDecodedRow)) {
                char line[100];
                sprintf(line, "mission-context catalogue=%u row=%u view=%u",
                    index, row, MenuView);
                Log(line);
                lastDecodedCatalogue = index;
                lastDecodedRow = row;
            }
            return ((unsigned long long)row << 32) | index;
        }
        row -= size;
    }
    return ~(unsigned long long)0;
}

static void SetView(unsigned view)
{
    char line[100];
    MenuView = view;
    WORD_AT(WORD_AT(0x8aea10) + 0xe8) = view;
    sprintf(line, "view=%u (0=official,2=categories,3=multi,4=user,5=exploration)", view);
    Log(line);
}

static void SetControlVisible(unsigned target, unsigned visible)
{
    unsigned message[6] = {0, 0, 0, 0, 0, 0};
    message[0] = target;
    message[1] = visible ? 0x01000003 : 0x01000004;
    if (target) GamePostMenuMessage(message);
}

/* The engine constructs definitions once, then reuses their live controls.
 * Run AFTER the stock refresh and use its queue so both the text and scene
 * visibility change together. Calling a scene vtable on a definition crashes.
 */
EXPORT void MenuApplyLayout(unsigned view)
{
    static const unsigned browserControls[] = {
        0x14200000, /* preview */
        0x14300000, /* description */
        0x14400000, /* Start */
        0x14600000, /* scrollbar */
        0x14700000, /* campaign group */
        0x14800000, /* mission group */
        0x14900000, /* List of missions */
        0x14b00000  /* Resume */
    };
    unsigned index, categories = view == 2;
    for (index = 0; index < 3; index++)
        SetControlVisible(MenuCategoryIds[index], categories);
    for (index = 0; index < sizeof(browserControls) / sizeof(browserControls[0]); index++)
        SetControlVisible(browserControls[index], !categories);
    SetControlVisible(0x14500000, 1); /* real bottom Back */
    SetControlVisible(0x14c00000, 0); /* secondary Back is hidden in stock */
    if (!categories) {
        /* ADD_ROW while the group is hidden intentionally does not refresh its
         * children. SHOW only reveals the parent, not rows hidden by CLEAR.
         * Reflow AFTER SHOW, through the same ordered engine queue. */
        unsigned refresh[6] = {0x14800000, 0x0200002c, 0, 0, 0, 0};
        GamePostMenuMessage(refresh);
    }
}

EXPORT void MenuMissionReady(void *screen, void *scene)
{
    unsigned index;
    char line[180];
    MenuMissionScreen = screen;
    MenuMissionScene = scene;
    for (index=0;index<3;index++)
        MenuCategoryIds[index] = MenuCategoryControls[index]
            ? WORD_AT((unsigned)MenuCategoryControls[index] + 8) : 0;
    sprintf(line, "mission-ready view=%u controls=%p,%p,%p", MenuView,
        MenuCategoryControls[0], MenuCategoryControls[1],
        MenuCategoryControls[2]);
    Log(line);
}

EXPORT void MenuEnter(void)
{
    SetView(2);
}

EXPORT void MenuLeave(void)
{
    SetView(0);
}

/* Click callbacks never overwrite the live control's routing ID (+0x60).
 * Queue a private application event, leaving visibility targeting intact. */
EXPORT void MenuCategoryClick(unsigned index)
{
    unsigned message[6] = {0, 0, 0, 0, 0, 0};
    if (index >= 3 || MenuView != 2) return;
    message[1] = 0x02000ff1 + index;
    GamePostMenuMessage(message);
}

EXPORT unsigned MenuHandleCategoryEvent(unsigned event, void *screen)
{
    static const unsigned views[] = {4, 3, 5};
    unsigned index = event - 0x02000ff1;
    if (index >= 3) return 0;
    if (MenuView == 2 && screen && GameCurrentScreenId() == 0x14000000) {
        SetView(views[index]);
        GameReload(screen);
    }
    return 1;
}

/* The global manager consumes Back before the screen event handler runs.
 * Intercept only the live mission browser; nested screens keep native Back. */
EXPORT unsigned MenuHandleBack(void *screen)
{
    if (MenuView < 2 || GameCurrentScreenId() != 0x14000000) return 0;
    if (MenuView >= 3) {
        SetView(2);
        GameReload(screen);
        return 1;
    }
    MenuLeave();
    return 0;
}

/* Return value for HookAction:
 * 0 = rebuild the native Single Mission screen through its normal transition;
 * 1 = action handled here;
 * 2 = category Back, continue as the native 0x0CC00000 Back action.
 */
EXPORT unsigned MenuActivateAction(unsigned action)
{
    unsigned view;
    if (action == 0x0cd10000) view = 4;      /* player-created */
    else if (action == 0x0cd20000) view = 3; /* MP -> solo */
    else if (action == 0x0cd30000) view = 5; /* exploration */
    else if (action == 0x0cd40000) {
        if (MenuView >= 3) {
            SetView(2);
            return 0;
        }
        MenuLeave();
        return 2;
    } else if (action == 0x0cd00000) {
        MenuEnter();
        return 0;
    } else return 1;
    if (MenuView != 2 || !MenuMissionScreen) return 1;
    SetView(view);
    return 0;
}

EXPORT int MenuRow(void *screen, void *control)
{
    (void)screen;
    (void)control;
    /* No list row is valid on the menu-style category screen. */
    return MenuView == 2;
}

typedef struct {
    unsigned address;
    unsigned length;
    const unsigned char *expected;
    void (*replacement)(void);
    unsigned char saved[32];
} MenuHook;

#define HOOK(address, bytes, function) {address, sizeof(bytes)-1, (const unsigned char *)bytes, function, {0}}
EXPORT MenuHook MenuHooks[] = {
    HOOK(0x625c81, "\x8b\xce\x68\xc0\xeb\x83\x00", HookBuild),
    HOOK(0x639afe, "\x83\xc4\x24\xb8\x01\x00\x00\x00", HookMissionBuild),
    HOOK(0x63c090, "\x3d\x00\x00\xc0\x0c", HookAction),
    HOOK(0x638e21, "\x8b\x41\x04\x25\xff\x0f\x00\x03", HookEventDispatch),
    HOOK(0x66cd70, "\x3d\x03\x00\x00\x02", HookBackDispatch),
    HOOK(0x63ae00, "\x8b\x35\x10\xea\x8a\x00\x33\xff", HookListBegin),
    HOOK(0x63ae61, "\x8b\x4c\x24\x18\x53\xe8\xe5\xe4\x07\x00", HookListOffset),
    HOOK(0x63a3de, "\x6a\x00\x8b\xcd\xe8\x69\xef\x07\x00", HookLabelOffset),
    HOOK(0x639d68, "\x3b\xe8\x0f\x8d\xf6\x03\x00\x00", HookOfficialGroups),
    HOOK(0x63aefa, "\x40\x89\x44\x24\x10", HookListNext),
    HOOK(0x63b310, "\x64\xa1\x00\x00\x00\x00", HookRowClick),
    HOOK(0x63b359, "\x33\xc9\x3b\xf0\x0f\x9d\xc1\x3b\xf0\x89\x4c\x24\x14\x7c\x0a\x8b\xd6\x2b\xd0\x89\x54\x24\x48\xeb\x06\x89\x74\x24\x48\x8b\xd6", HookRowDecode),
    HOOK(0x6390c9, "\x89\x91\xe8\x00\x00\x00", HookSelect),
    HOOK(0x63be2c, "\xa1\x34\xea\x8a\x00", HookNativeSingle),
    HOOK(0x63be73, "\xa1\x34\xea\x8a\x00", HookNativeCarnage),
    HOOK(0x6b6912, "\xc7\x80\xe8\x00\x00\x00\x01\x00\x00\x00", HookCatalogueReset),
    HOOK(0x63abec, "\x89\x5c\x24\x30\xc7\x44\x24\x1c\x00\x00\x10\x14", HookTitle),
    HOOK(0x63af06, "\x8b\x4c\x24\x34\x5f", HookRefreshDone)
};
EXPORT const unsigned MenuHookCount = sizeof(MenuHooks) / sizeof(MenuHooks[0]);

/* Windows may report the executable path in lowercase (notably when launched
 * using a process identifier). Its spelling must not disable menus/diagnostics. */
EXPORT unsigned MenuExecutableKind(const char *name)
{
    if (!stricmp(name, "HD2_SabreSquadron.exe")) return 2;
    if (!stricmp(name, "HD2.exe")) return 1;
    return 0;
}

EXPORT void InitializeASI(void)
{
    unsigned index, count = sizeof(MenuHooks) / sizeof(MenuHooks[0]);
    int isSabre;
    DWORD oldProtect, unused;
    char *slash;
    if (InterlockedCompareExchange(&initialized, 1, 0)) return;
    GetModuleFileNameA(NULL, logPath, sizeof(logPath));
    slash = strrchr(logPath, '\\');
    if (!slash) return;
    index = MenuExecutableKind(slash + 1);
    if (!index) return;
    isSabre = index == 2;
    strcpy(slash + 1, "HD2.CustomMenu.log");
    StartDiagnostics();
    if (!isSabre) {
        Log("Diagnostic monitor started for base H&D2; custom menu hooks are Sabre-only.");
        return;
    }
    Log("Native Custom Missions menu module initialized (native queue v2).");
    if ((unsigned)GetModuleHandleA(NULL) != 0x400000) {
        Log("Unsupported image base. No changes applied.");
        return;
    }
    /* All-or-nothing signature check, before altering any code. No asynchronous
     * patching thread: UAL must call this once the stock client is unpacked.
     */
    for (index = 0; index < count; index++) {
        MenuHook *hook = &MenuHooks[index];
        if (memcmp((void *)hook->address, hook->expected, hook->length)) {
            char line[100];
            sprintf(line, "Signature mismatch at %08X; no changes applied.", hook->address);
            Log(line);
            return;
        }
        memcpy(hook->saved, (void *)hook->address, hook->length);
    }
    for (index = 0; index < count; index++) {
        MenuHook *hook = &MenuHooks[index];
        if (!VirtualProtect((void *)hook->address, hook->length, PAGE_EXECUTE_READWRITE, &oldProtect)) break;
        memset((void *)hook->address, 0x90, hook->length);
        *(unsigned char *)hook->address = 0xe9;
        WORD_AT(hook->address + 1) = (unsigned)hook->replacement - hook->address - 5;
        FlushInstructionCache(GetCurrentProcess(), (void *)hook->address, hook->length);
        VirtualProtect((void *)hook->address, hook->length, oldProtect, &unused);
    }
    if (index != count) {
        while (index) {
            MenuHook *hook = &MenuHooks[--index];
            if (VirtualProtect((void *)hook->address, hook->length, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                memcpy((void *)hook->address, hook->saved, hook->length);
                FlushInstructionCache(GetCurrentProcess(), (void *)hook->address, hook->length);
                VirtualProtect((void *)hook->address, hook->length, oldProtect, &unused);
            }
        }
        Log("Could not install complete menu; reverted installed hooks.");
        return;
    }
    Log("Menu routes installed. This log is not a GUI test result.");
}

BOOL WINAPI DllMain(HINSTANCE instance, DWORD reason, LPVOID reserved)
{
    if (reason == DLL_PROCESS_ATTACH) DisableThreadLibraryCalls(instance);
    return TRUE;
}
