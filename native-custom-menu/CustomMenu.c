/* H&D2 1.12 native custom-mission menu, loaded by Ultimate ASI Loader.
 * Does not rewrite the game EXE, start a game, or open another process.
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
EXPORT const char MenuBackControlName[] = "bcustom back";
EXPORT void *MenuMissionScreen;
EXPORT void *MenuMissionScene;
EXPORT void *MenuCategoryControls[4];
EXPORT void *MenuBackControl;
EXPORT void *MenuStartControl;
EXPORT void *MenuCaptionControl;
EXPORT void *MenuResumeControl;
static LONG initialized;
static char logPath[MAX_PATH];

extern int GameCount(unsigned catalogue);
extern void GameReload(void *screen);
extern void *GameFindNode(void *scene, const char *name);
extern void GameSetNodeVisible(void *node, unsigned visible);
EXPORT unsigned MenuActivateAction(unsigned action);
EXPORT void HookBuild(void);
EXPORT void HookCustomCallback(void);
EXPORT void HookPlayerCallback(void);
EXPORT void HookMultiCallback(void);
EXPORT void HookExploreCallback(void);
EXPORT void HookBackCallback(void);
EXPORT void HookNativeBackEvent(void);
EXPORT void HookMissionBuild(void);
EXPORT void HookStartLabel(void);
EXPORT void HookListCaption(void);
EXPORT void HookResumeLabel(void);
EXPORT void HookAction(void);
EXPORT void HookEventDispatch(void);
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
        if (row < (unsigned)size)
            return ((unsigned long long)row << 32) | index;
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

static void SetNode(const char *name, unsigned visible)
{
    void *node;
    if (!MenuMissionScene) return;
    node = GameFindNode(MenuMissionScene, name);
    if (node) GameSetNodeVisible(node, visible);
}

EXPORT void MenuSetControlVisible(void *control, unsigned visible)
{
    if (control) GameSetNodeVisible(control, visible);
}

/* The category selector is deliberately not a mission list. It uses four
 * native button controls added to the mission scene. The normal browser
 * furniture is restored unchanged for the three actual mission lists.
 */
EXPORT void MenuApplyLayout(unsigned view)
{
    static const char *categoryNodes[] = {
        "bcustom user", "bcustom multi", "bcustom explore"
    };
    static const char *categoryVisuals[] = {
        "normal11", "actived11", "normal12", "actived12",
        "normal13", "actived13"
    };
    static const char *browserNodes[] = {
        "table01", "scroll00", "text_list of profiles",
        "bload mission", "bload lastsave", "bshort", "blong",
        "bexit01"
    };
    unsigned index, categories = view == 2;
    for (index = 0; index < sizeof(categoryNodes) / sizeof(categoryNodes[0]); index++) {
        SetNode(categoryNodes[index], categories);
        /* Runtime labels are attached to the resolved control, not to the
         * cloned 4DS children. Hide the control itself as well so a rebuilt
         * detail list cannot leave a bare category label behind. */
        MenuSetControlVisible(MenuCategoryControls[index], categories);
    }
    for (index = 0; index < sizeof(categoryVisuals) / sizeof(categoryVisuals[0]); index++)
        SetNode(categoryVisuals[index], categories && !(index & 1));
    for (index = 0; index < sizeof(browserNodes) / sizeof(browserNodes[0]); index++)
        SetNode(browserNodes[index], !categories);
    /* The stock Start/Resume labels are runtime controls. Their 4DS roots can
     * be hidden while the text remains visible, producing the duplicate Back
     * row seen in game. Apply visibility to both layers. */
    MenuSetControlVisible(MenuStartControl, !categories);
    MenuSetControlVisible(MenuCaptionControl, !categories);
    MenuSetControlVisible(MenuResumeControl, !categories);
    MenuSetControlVisible(MenuBackControl, 1);
    if (categories) {
        static const char *browserVisuals[] = {
            "normal03", "actived03", "normal05", "actived05",
            "normal06", "actived06", "normal07", "actived07"
        };
        for (index = 0; index < sizeof(browserVisuals) / sizeof(browserVisuals[0]); index++)
            SetNode(browserVisuals[index], 0);
        SetNode("screen_shot", 0);
        SetNode("video", 0);
        SetNode("panel", 0);
    } else {
        SetNode("panel", 1);
    }
}

EXPORT void MenuMissionReady(void *screen, void *scene)
{
    char line[180];
    MenuMissionScreen = screen;
    MenuMissionScene = scene;
    sprintf(line, "mission-ready view=%u controls=%p,%p,%p", MenuView,
        MenuCategoryControls[0], MenuCategoryControls[1],
        MenuCategoryControls[2]);
    Log(line);
    MenuApplyLayout(MenuView);
}

EXPORT void MenuPrepareControl(void *control)
{
    unsigned index;
    if (!control) return;
    for (index = 0; index < 3; index++) {
        if (control == MenuCategoryControls[index]) {
            WORD_AT((unsigned)control + 0x60) = 0x0cd00000;
            return;
        }
    }
}

EXPORT void MenuEnter(void)
{
    SetView(2);
    MenuApplyLayout(2);
}

EXPORT void MenuLeave(void)
{
    SetView(0);
    MenuApplyLayout(0);
}

/* Return value for HookAction:
 * 0 = rebuild the native Single Mission screen through its normal transition;
 * 1 = action handled here;
 * 2 = category Back, continue as the native 0x0CC00000 Back action.
 */
EXPORT unsigned MenuActivateControl(void *control)
{
    if (control == MenuCategoryControls[0]) return MenuActivateAction(0x0cd10000);
    if (control == MenuCategoryControls[1]) return MenuActivateAction(0x0cd20000);
    if (control == MenuCategoryControls[2]) return MenuActivateAction(0x0cd30000);
    if (control == MenuCategoryControls[3]) return MenuActivateAction(0x0cd40000);
    return MenuActivateAction(0x0cd00000);
}

EXPORT unsigned MenuActivateAction(unsigned action)
{
    unsigned view;
    if (action == 0x0cd10000) view = 4;      /* player-created */
    else if (action == 0x0cd20000) view = 3; /* MP -> solo */
    else if (action == 0x0cd30000) view = 5; /* exploration */
    else if (action == 0x0cd40000) {
        if (MenuView >= 3) {
            SetView(2);
            MenuApplyLayout(2);
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
    MenuApplyLayout(view);
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
    HOOK(0x639aef, "\x6a\x00\x68\x04\x00\x00\x01", HookNativeBackEvent),
    HOOK(0x6396fe, "\x68\x35\x09\x00\x00", HookStartLabel),
    HOOK(0x639a17, "\x68\xd2\x08\x00\x00", HookListCaption),
    HOOK(0x639a94, "\x68\x39\x08\x00\x00", HookResumeLabel),
    HOOK(0x63c090, "\x3d\x00\x00\xc0\x0c", HookAction),
    HOOK(0x638e21, "\x8b\x41\x04\x25\xff\x0f\x00\x03", HookEventDispatch),
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

EXPORT void InitializeASI(void)
{
    unsigned index, count = sizeof(MenuHooks) / sizeof(MenuHooks[0]);
    DWORD oldProtect, unused;
    char *slash;
    if (InterlockedCompareExchange(&initialized, 1, 0)) return;
    GetModuleFileNameA(NULL, logPath, sizeof(logPath));
    slash = strrchr(logPath, '\\');
    if (!slash || strcmp(slash + 1, "HD2_SabreSquadron.exe")) return;
    strcpy(slash + 1, "HD2.CustomMenu.log");
    Log("Native Custom Missions menu module initialized.");
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
