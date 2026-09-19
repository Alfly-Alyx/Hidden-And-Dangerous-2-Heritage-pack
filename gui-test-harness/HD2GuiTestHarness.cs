using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

internal static class HD2GuiTestHarness
{
    private const uint ProcessQueryLimitedInformation = 0x1000;
    private const uint ProcessVmRead = 0x0010;
    private const int SwRestore = 9;
    private const uint InputMouse = 0;
    private const uint InputKeyboard = 1;
    private const uint MouseeventfMove = 0x0001;
    private const uint MouseeventfLeftdown = 0x0002;
    private const uint MouseeventfLeftup = 0x0004;
    private const uint MouseeventfVirtualdesk = 0x4000;
    private const uint MouseeventfAbsolute = 0x8000;
    private const uint KeyeventfKeyup = 0x0002;
    private const uint WmMousemove = 0x0200;
    private const uint WmLbuttondown = 0x0201;
    private const uint WmLbuttonup = 0x0202;
    private const int MkLbutton = 0x0001;
    private const uint WmClose = 0x0010;
    private const uint EsContinuous = 0x80000000;
    private const uint EsSystemRequired = 0x00000001;
    private const uint EsDisplayRequired = 0x00000002;

    [StructLayout(LayoutKind.Sequential)]
    private struct Rect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct Point
    {
        public int X;
        public int Y;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct Input
    {
        public uint Type;
        public InputUnion Union;
    }

    [StructLayout(LayoutKind.Explicit)]
    private struct InputUnion
    {
        [FieldOffset(0)] public MouseInput Mouse;
        [FieldOffset(0)] public KeyboardInput Keyboard;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct MouseInput
    {
        public int Dx;
        public int Dy;
        public uint MouseData;
        public uint Flags;
        public uint Time;
        public IntPtr ExtraInfo;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct KeyboardInput
    {
        public ushort Vk;
        public ushort Scan;
        public uint Flags;
        public uint Time;
        public IntPtr ExtraInfo;
    }

    private delegate bool EnumWindowsProc(IntPtr window, IntPtr parameter);

    [DllImport("user32.dll")]
    private static extern bool SetProcessDPIAware();

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr parameter);

    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr window);

    [DllImport("user32.dll")]
    private static extern bool IsWindow(IntPtr window);

    [DllImport("user32.dll")]
    private static extern bool IsIconic(IntPtr window);

    [DllImport("user32.dll")]
    private static extern bool GetWindowRect(IntPtr window, out Rect rect);

    [DllImport("user32.dll")]
    private static extern bool GetClientRect(IntPtr window, out Rect rect);

    [DllImport("user32.dll")]
    private static extern bool ClientToScreen(IntPtr window, ref Point point);

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);

    [DllImport("user32.dll")]
    private static extern bool AttachThreadInput(uint attach, uint attachTo, bool attachState);

    [DllImport("kernel32.dll")]
    private static extern uint GetCurrentThreadId();

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowText(IntPtr window, StringBuilder text, int maxCount);

    [DllImport("user32.dll")]
    private static extern bool ShowWindow(IntPtr window, int command);

    [DllImport("user32.dll")]
    private static extern bool BringWindowToTop(IntPtr window);

    [DllImport("user32.dll")]
    private static extern bool SetForegroundWindow(IntPtr window);

    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    private static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    private static extern bool GetCursorPos(out Point point);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint SendInput(uint count, Input[] inputs, int size);

    [DllImport("user32.dll")]
    private static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);

    [DllImport("user32.dll")]
    private static extern uint MapVirtualKey(uint code, uint mapType);

    [DllImport("user32.dll")]
    private static extern int GetSystemMetrics(int index);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool PostMessage(IntPtr window, uint message, IntPtr wParam, IntPtr lParam);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint access, bool inheritHandle, uint processId);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool QueryFullProcessImageName(IntPtr process, uint flags, StringBuilder exeName, ref uint size);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadProcessMemory(IntPtr process, IntPtr address, byte[] buffer, int size, out IntPtr bytesRead);

    [DllImport("kernel32.dll")]
    private static extern bool CloseHandle(IntPtr handle);

    [DllImport("kernel32.dll")]
    private static extern uint SetThreadExecutionState(uint flags);

    public static int Main(string[] args)
    {
        try
        {
            SetProcessDPIAware();
            if (args.Length == 0)
                return Usage("Commande manquante.");

            string command = args[0].ToLowerInvariant();
            Dictionary<string, string> options = ParseOptions(args, 1);
            if (command == "launch")
                return Launch(options);
            if (command == "wake")
                return Wake(options);
            if (command == "info")
                return Info(options);
            if (command == "capture")
                return Capture(options);
            if (command == "key")
                return Key(options);
            if (command == "click")
                return Click(options);
            if (command == "move")
                return Move(options);
            if (command == "relmove")
                return RelativeMove(options, false);
            if (command == "relclick")
                return RelativeMove(options, true);
            if (command == "legacyclick")
                return LegacyClick(options);
            if (command == "rellegacyclick")
                return RelativeLegacyClick(options);
            if (command == "abslegacyclick")
                return AbsoluteLegacyClick(options);
            if (command == "sendabsclick")
                return SendAbsoluteClick(options);
            if (command == "legacyrelmove")
                return LegacyRelativeMove(options, false);
            if (command == "legacyrelclick")
                return LegacyRelativeMove(options, true);
            if (command == "legacycombinedclick")
                return LegacyCombinedClick(options);
            if (command == "legacydragclick")
                return LegacyDragClick(options);
            if (command == "postclick")
                return PostClick(options);
            if (command == "cursor")
                return CursorInfo(options);
            if (command == "dump")
                return DumpMemory(options);
            if (command == "close")
                return Close(options);
            return Usage("Commande inconnue : " + command);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("ERREUR: " + ex.Message);
            return 1;
        }
    }

    private static int Launch(Dictionary<string, string> options)
    {
        string game = RequirePath(options, "game");
        string state = RequireValue(options, "state");
        int timeoutSeconds = GetInt(options, "timeout", 45);
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(state)));

        ProcessStartInfo start = new ProcessStartInfo();
        start.FileName = game;
        start.WorkingDirectory = Path.GetDirectoryName(game);
        start.UseShellExecute = false;
        Process process = Process.Start(start);
        if (process == null)
            throw new InvalidOperationException("Le processus du jeu n'a pas été créé.");

        DateTime deadline = DateTime.UtcNow.AddSeconds(timeoutSeconds);
        IntPtr window = IntPtr.Zero;
        while (DateTime.UtcNow < deadline)
        {
            if (process.HasExited)
                throw new InvalidOperationException("Le jeu s'est fermé avec le code " + process.ExitCode + ".");
            window = FindLargestWindow(process.Id);
            if (window != IntPtr.Zero)
                break;
            Thread.Sleep(250);
        }
        if (window == IntPtr.Zero)
            throw new TimeoutException("Aucune fenêtre visible du jeu après " + timeoutSeconds + " secondes.");

        string actual = GetProcessPath(process.Id);
        RequireSamePath(game, actual);
        File.WriteAllLines(state, new[]
        {
            "pid=" + process.Id.ToString(CultureInfo.InvariantCulture),
            "game=" + actual,
            "hwnd=" + window.ToInt64().ToString(CultureInfo.InvariantCulture),
            "startedUtc=" + process.StartTime.ToUniversalTime().Ticks.ToString(CultureInfo.InvariantCulture)
        }, Encoding.UTF8);
        Console.WriteLine("LAUNCHED pid={0} hwnd=0x{1:X} game={2}", process.Id, window.ToInt64(), actual);
        if (options.ContainsKey("startup-output"))
        {
            SaveClientScreenshot(window, options["startup-output"]);
            Console.WriteLine("STARTUP_CAPTURED " + Path.GetFullPath(options["startup-output"]));
        }
        int startupEscapes = GetInt(options, "startup-esc", 0);
        if (startupEscapes > 0)
        {
            ShowWindow(window, SwRestore);
            BringWindowToTop(window);
            SetForegroundWindow(window);
            for (int i = 0; i < startupEscapes; i++)
            {
                SendKey(0x1B);
                Thread.Sleep(GetInt(options, "startup-interval", 500));
            }
            Console.WriteLine("STARTUP_ESC_SENT repeat={0}", startupEscapes);
        }
        if (GetInt(options, "hold", 0) != 0)
        {
            int seconds = 0;
            bool keepForeground = GetInt(options, "keep-foreground", 0) != 0;
            while (!process.WaitForExit(keepForeground ? 100 : 1000))
            {
                if (keepForeground)
                {
                    IntPtr currentWindow = FindLargestWindow(process.Id);
                    if (currentWindow == IntPtr.Zero && IsOwnedWindow(window, process.Id))
                        currentWindow = window;
                    if (currentWindow != IntPtr.Zero)
                    {
                        BringWindowToTop(currentWindow);
                        SetForegroundWindow(currentWindow);
                    }
                }
                seconds++;
                int ticksPerSecond = keepForeground ? 10 : 1;
                if (options.ContainsKey("record-dir") && seconds % (3 * ticksPerSecond) == 0 && seconds <= 30 * ticksPerSecond)
                {
                    IntPtr current = FindLargestWindow(process.Id);
                    if (current == IntPtr.Zero && IsOwnedWindow(window, process.Id))
                        current = window;
                    if (current != IntPtr.Zero && GetForegroundWindow() == current)
                    {
                        string shot = Path.Combine(options["record-dir"], "startup-" + seconds.ToString("D2") + ".jpg");
                        try
                        {
                            SaveClientScreenshot(current, shot);
                            Console.WriteLine("OBSERVED " + shot);
                        }
                        catch (Exception ex) { Console.WriteLine("TRANSITION " + ex.Message); }
                    }
                }
            }
            Console.WriteLine("GAME_EXIT code={0} hex=0x{1:X8}", process.ExitCode, process.ExitCode);
        }
        return 0;
    }

    private static int Wake(Dictionary<string, string> options)
    {
        SetThreadExecutionState(EsContinuous | EsSystemRequired | EsDisplayRequired);
        mouse_event(MouseeventfMove, 1, 0, 0, UIntPtr.Zero);
        Thread.Sleep(100);
        mouse_event(MouseeventfMove, unchecked((uint)-1), 0, 0, UIntPtr.Zero);
        Thread.Sleep(GetInt(options, "delay", 1000));
        Console.WriteLine("DISPLAY_WAKE_SENT");
        return 0;
    }

    private static int Info(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        IntPtr window = FindTargetWindow(target);
        if (window == IntPtr.Zero)
            throw new InvalidOperationException("La fenêtre du processus autorisé est introuvable.");
        Rect rect;
        GetWindowRect(window, out rect);
        Rect client;
        GetClientRect(window, out client);
        StringBuilder title = new StringBuilder(512);
        GetWindowText(window, title, title.Capacity);
        Console.WriteLine("pid={0}", target.Pid);
        Console.WriteLine("game={0}", target.Game);
        Console.WriteLine("hwnd=0x{0:X}", window.ToInt64());
        Console.WriteLine("title={0}", title.ToString());
        Console.WriteLine("window={0},{1},{2},{3}", rect.Left, rect.Top, rect.Right - rect.Left, rect.Bottom - rect.Top);
        Console.WriteLine("client={0},{1}", client.Right - client.Left, client.Bottom - client.Top);
        Console.WriteLine("foreground={0}", GetForegroundWindow() == window ? "yes" : "no");
        return 0;
    }

    private static int Capture(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        string output = RequireValue(options, "output");
        IntPtr window = ActivateVerifiedWindow(target);
        Thread.Sleep(GetInt(options, "delay", 400));
        SaveClientScreenshot(window, output);
        Console.WriteLine("CAPTURED " + Path.GetFullPath(output));
        return 0;
    }

    private static int Key(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        ushort vk = ParseVirtualKey(RequireValue(options, "name"));
        int repeat = GetInt(options, "repeat", 1);
        int interval = GetInt(options, "interval", 250);
        IntPtr window = ActivateVerifiedWindow(target);
        for (int i = 0; i < repeat; i++)
        {
            RequireForeground(window, target.Pid);
            SendKey(vk);
            if (i + 1 < repeat)
                Thread.Sleep(interval);
        }
        Thread.Sleep(GetInt(options, "delay", 500));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("KEY_SENT name={0} repeat={1}", options["name"], repeat);
        return 0;
    }

    private static int Click(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        int x = GetInt(options, "x", -1);
        int y = GetInt(options, "y", -1);
        if (x < 0 || y < 0)
            throw new ArgumentException("Les coordonnées --x et --y sont requises et doivent être positives.");
        IntPtr window = ActivateVerifiedWindow(target);
        Rect client;
        if (!GetClientRect(window, out client))
            throw new InvalidOperationException("Impossible de lire la zone cliente du jeu.");
        if (x >= client.Right || y >= client.Bottom)
            throw new ArgumentOutOfRangeException("Coordonnées hors de la fenêtre du jeu.");
        Point origin = new Point { X = 0, Y = 0 };
        if (!ClientToScreen(window, ref origin))
            throw new InvalidOperationException("Impossible de convertir les coordonnées du jeu.");
        RequireForeground(window, target.Pid);
        SetCursorPos(origin.X + x, origin.Y + y);
        Input[] input = new Input[2];
        input[0].Type = InputMouse;
        input[0].Union.Mouse.Flags = MouseeventfLeftdown;
        input[1].Type = InputMouse;
        input[1].Union.Mouse.Flags = MouseeventfLeftup;
        Thread.Sleep(100);
        if (SendInput(1, new[] { input[0] }, Marshal.SizeOf(typeof(Input))) != 1)
            throw new InvalidOperationException("Le clic n'a pas été envoyé.");
        Thread.Sleep(100);
        if (SendInput(1, new[] { input[1] }, Marshal.SizeOf(typeof(Input))) != 1)
            throw new InvalidOperationException("Le relâchement du clic n'a pas été envoyé.");
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("CLICK_SENT x={0} y={1}", x, y);
        return 0;
    }

    private static int Move(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        int x = GetInt(options, "x", -1);
        int y = GetInt(options, "y", -1);
        if (x < 0 || y < 0)
            throw new ArgumentException("Les coordonnées --x et --y sont requises et doivent être positives.");
        IntPtr window = ActivateVerifiedWindow(target);
        Rect client;
        if (!GetClientRect(window, out client))
            throw new InvalidOperationException("Impossible de lire la zone cliente du jeu.");
        if (x >= client.Right || y >= client.Bottom)
            throw new ArgumentOutOfRangeException("Coordonnées hors de la fenêtre du jeu.");
        Point origin = new Point { X = 0, Y = 0 };
        if (!ClientToScreen(window, ref origin))
            throw new InvalidOperationException("Impossible de convertir les coordonnées du jeu.");
        RequireForeground(window, target.Pid);
        SetCursorPos(origin.X + x, origin.Y + y);
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("MOUSE_MOVED x={0} y={1}", x, y);
        return 0;
    }

    private static int RelativeMove(Dictionary<string, string> options, bool click)
    {
        Target target = GetTarget(options);
        int dx = GetInt(options, "dx", 0);
        int dy = GetInt(options, "dy", 0);
        IntPtr window = ActivateVerifiedWindow(target);
        RequireForeground(window, target.Pid);
        Input move = new Input();
        move.Type = InputMouse;
        move.Union.Mouse.Dx = dx;
        move.Union.Mouse.Dy = dy;
        move.Union.Mouse.Flags = MouseeventfMove;
        if (SendInput(1, new[] { move }, Marshal.SizeOf(typeof(Input))) != 1)
            throw new InvalidOperationException("Le déplacement relatif n'a pas été envoyé.");
        Thread.Sleep(250);
        if (click)
        {
            Input down = new Input();
            down.Type = InputMouse;
            down.Union.Mouse.Flags = MouseeventfLeftdown;
            Input up = new Input();
            up.Type = InputMouse;
            up.Union.Mouse.Flags = MouseeventfLeftup;
            if (SendInput(1, new[] { down }, Marshal.SizeOf(typeof(Input))) != 1)
                throw new InvalidOperationException("Le clic relatif n'a pas été envoyé.");
            Thread.Sleep(100);
            if (SendInput(1, new[] { up }, Marshal.SizeOf(typeof(Input))) != 1)
                throw new InvalidOperationException("Le relâchement du clic relatif n'a pas été envoyé.");
        }
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("MOUSE_RELATIVE dx={0} dy={1} click={2}", dx, dy, click ? 1 : 0);
        return 0;
    }

    private static int LegacyClick(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        IntPtr window = ActivateVerifiedWindow(target);
        RequireForeground(window, target.Pid);
        mouse_event(MouseeventfLeftdown, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(100);
        mouse_event(MouseeventfLeftup, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("LEGACY_CLICK_SENT");
        return 0;
    }

    private static void SendRelativeMouse(int dx, int dy)
    {
        Input move = new Input();
        move.Type = InputMouse;
        move.Union.Mouse.Dx = dx;
        move.Union.Mouse.Dy = dy;
        move.Union.Mouse.Flags = MouseeventfMove;
        if (SendInput(1, new[] { move }, Marshal.SizeOf(typeof(Input))) != 1)
            throw new InvalidOperationException("Le déplacement relatif n'a pas été envoyé.");
    }

    private static int RelativeLegacyClick(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        int x = GetInt(options, "x", -1);
        int y = GetInt(options, "y", -1);
        if (x < 0 || y < 0)
            throw new ArgumentException("Les coordonnées --x et --y sont requises et doivent être positives.");
        IntPtr window = ActivateVerifiedWindow(target);
        RequireForeground(window, target.Pid);
        SendRelativeMouse(-5000, -5000);
        Thread.Sleep(250);
        SendRelativeMouse(x, y);
        Thread.Sleep(250);
        mouse_event(MouseeventfLeftdown, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(100);
        mouse_event(MouseeventfLeftup, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("RELATIVE_LEGACY_CLICK x={0} y={1}", x, y);
        return 0;
    }

    private static int AbsoluteLegacyClick(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        int x = GetInt(options, "x", -1);
        int y = GetInt(options, "y", -1);
        if (x < 0 || y < 0)
            throw new ArgumentException("Les coordonnées --x et --y sont requises et doivent être positives.");
        IntPtr window = ActivateVerifiedWindow(target);
        Rect client;
        if (!GetClientRect(window, out client) || x >= client.Right || y >= client.Bottom)
            throw new ArgumentOutOfRangeException("Coordonnées hors de la fenêtre du jeu.");
        Point origin = new Point { X = 0, Y = 0 };
        if (!ClientToScreen(window, ref origin))
            throw new InvalidOperationException("Impossible de convertir les coordonnées du jeu.");
        RequireForeground(window, target.Pid);
        SetCursorPos(origin.X + x, origin.Y + y);
        Thread.Sleep(GetInt(options, "move-delay", 250));
        mouse_event(MouseeventfLeftdown, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(100);
        mouse_event(MouseeventfLeftup, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("ABSOLUTE_LEGACY_CLICK x={0} y={1}", x, y);
        return 0;
    }

    private static int SendAbsoluteClick(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        int x = GetInt(options, "x", -1);
        int y = GetInt(options, "y", -1);
        if (x < 0 || y < 0)
            throw new ArgumentException("Les coordonnées --x et --y sont requises et doivent être positives.");
        IntPtr window = ActivateVerifiedWindow(target);
        Point origin = new Point { X = 0, Y = 0 };
        if (!ClientToScreen(window, ref origin))
            throw new InvalidOperationException("Impossible de convertir les coordonnées du jeu.");
        RequireForeground(window, target.Pid);
        int left = GetSystemMetrics(76);
        int top = GetSystemMetrics(77);
        int width = GetSystemMetrics(78);
        int height = GetSystemMetrics(79);
        int screenX = origin.X + x;
        int screenY = origin.Y + y;
        int normalizedX = (int)Math.Round((screenX - left) * 65535.0 / Math.Max(1, width - 1));
        int normalizedY = (int)Math.Round((screenY - top) * 65535.0 / Math.Max(1, height - 1));
        Input move = new Input();
        move.Type = InputMouse;
        move.Union.Mouse.Dx = normalizedX;
        move.Union.Mouse.Dy = normalizedY;
        move.Union.Mouse.Flags = MouseeventfMove | MouseeventfAbsolute | MouseeventfVirtualdesk;
        Input down = new Input();
        down.Type = InputMouse;
        down.Union.Mouse.Flags = MouseeventfLeftdown;
        Input up = new Input();
        up.Type = InputMouse;
        up.Union.Mouse.Flags = MouseeventfLeftup;
        Input[] batch = new[] { move, down, up };
        if (SendInput((uint)batch.Length, batch, Marshal.SizeOf(typeof(Input))) != batch.Length)
            throw new InvalidOperationException("Le clic absolu groupé n'a pas été envoyé.");
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("SEND_ABSOLUTE_CLICK x={0} y={1}", x, y);
        return 0;
    }

    private static int LegacyRelativeMove(Dictionary<string, string> options, bool click)
    {
        Target target = GetTarget(options);
        int dx = GetInt(options, "dx", 0);
        int dy = GetInt(options, "dy", 0);
        IntPtr window = ActivateVerifiedWindow(target);
        RequireForeground(window, target.Pid);
        mouse_event(MouseeventfMove, unchecked((uint)dx), unchecked((uint)dy), 0, UIntPtr.Zero);
        Thread.Sleep(250);
        if (click)
        {
            mouse_event(MouseeventfLeftdown, 0, 0, 0, UIntPtr.Zero);
            Thread.Sleep(100);
            mouse_event(MouseeventfLeftup, 0, 0, 0, UIntPtr.Zero);
        }
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("LEGACY_RELATIVE dx={0} dy={1} click={2}", dx, dy, click ? 1 : 0);
        return 0;
    }

    private static int LegacyCombinedClick(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        int dx = GetInt(options, "dx", 0);
        int dy = GetInt(options, "dy", 0);
        IntPtr window = ActivateVerifiedWindow(target);
        RequireForeground(window, target.Pid);
        mouse_event(MouseeventfMove | MouseeventfLeftdown,
            unchecked((uint)dx), unchecked((uint)dy), 0, UIntPtr.Zero);
        Thread.Sleep(GetInt(options, "hold", 120));
        mouse_event(MouseeventfLeftup, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("LEGACY_COMBINED_CLICK dx={0} dy={1}", dx, dy);
        return 0;
    }

    private static int LegacyDragClick(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        IntPtr window = ActivateVerifiedWindow(target);
        RequireForeground(window, target.Pid);
        int pulses = GetInt(options, "pulses", 12);
        mouse_event(MouseeventfLeftdown, 0, 0, 0, UIntPtr.Zero);
        for (int i = 0; i < pulses; i++)
        {
            int dx = (i & 1) == 0 ? 1 : -1;
            mouse_event(MouseeventfMove | MouseeventfLeftdown,
                unchecked((uint)dx), 0, 0, UIntPtr.Zero);
            Thread.Sleep(50);
        }
        mouse_event(MouseeventfLeftup, 0, 0, 0, UIntPtr.Zero);
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("LEGACY_DRAG_CLICK pulses={0}", pulses);
        return 0;
    }

    private static int PostClick(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        int x = GetInt(options, "x", -1);
        int y = GetInt(options, "y", -1);
        if (x < 0 || y < 0)
            throw new ArgumentException("Les coordonnées --x et --y sont requises et doivent être positives.");
        IntPtr window = ActivateVerifiedWindow(target);
        RequireForeground(window, target.Pid);
        IntPtr position = new IntPtr((y << 16) | (x & 0xffff));
        PostMessage(window, WmMousemove, IntPtr.Zero, position);
        PostMessage(window, WmLbuttondown, new IntPtr(MkLbutton), position);
        Thread.Sleep(100);
        PostMessage(window, WmLbuttonup, IntPtr.Zero, position);
        Thread.Sleep(GetInt(options, "delay", 700));
        if (options.ContainsKey("output"))
            SaveClientScreenshot(window, options["output"]);
        Console.WriteLine("POST_CLICK_SENT x={0} y={1}", x, y);
        return 0;
    }

    private static int CursorInfo(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        IntPtr window = ActivateVerifiedWindow(target);
        RequireForeground(window, target.Pid);
        Point point;
        if (!GetCursorPos(out point))
            throw new InvalidOperationException("Impossible de lire la position du curseur Windows.");
        Console.WriteLine("CURSOR x={0} y={1}", point.X, point.Y);
        return 0;
    }

    private static int DumpMemory(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        string addressText = RequireValue(options, "address");
        uint address = addressText.StartsWith("0x", StringComparison.OrdinalIgnoreCase)
            ? UInt32.Parse(addressText.Substring(2), NumberStyles.HexNumber, CultureInfo.InvariantCulture)
            : UInt32.Parse(addressText, NumberStyles.Integer, CultureInfo.InvariantCulture);
        int length = GetInt(options, "length", 0);
        string output = RequireValue(options, "output");
        if (length <= 0 || length > 1048576)
            throw new ArgumentOutOfRangeException("La longueur doit être comprise entre 1 et 1048576.");
        IntPtr process = OpenProcess(ProcessQueryLimitedInformation | ProcessVmRead, false, (uint)target.Pid);
        if (process == IntPtr.Zero)
            throw new InvalidOperationException("Impossible d'ouvrir le processus autorisé en lecture.");
        try
        {
            byte[] buffer = new byte[length];
            IntPtr read;
            if (!ReadProcessMemory(process, new IntPtr(unchecked((int)address)), buffer, length, out read) || read.ToInt64() != length)
                throw new InvalidOperationException("Impossible de lire la plage mémoire demandée.");
            string fullOutput = Path.GetFullPath(output);
            Directory.CreateDirectory(Path.GetDirectoryName(fullOutput));
            File.WriteAllBytes(fullOutput, buffer);
            Console.WriteLine("DUMPED address=0x{0:X8} length={1} output={2}", address, length, fullOutput);
        }
        finally
        {
            CloseHandle(process);
        }
        return 0;
    }

    private static int Close(Dictionary<string, string> options)
    {
        Target target = GetTarget(options);
        Process process = Process.GetProcessById(target.Pid);
        IntPtr window = FindTargetWindow(target);
        if (window != IntPtr.Zero)
            PostMessage(window, WmClose, IntPtr.Zero, IntPtr.Zero);
        if (!process.WaitForExit(GetInt(options, "timeout", 8) * 1000))
        {
            RequireSamePath(target.Game, GetProcessPath(target.Pid));
            process.Kill();
            process.WaitForExit(5000);
            Console.WriteLine("CLOSED_FORCED pid={0}", target.Pid);
        }
        else
        {
            Console.WriteLine("CLOSED_GRACEFULLY pid={0}", target.Pid);
        }
        return 0;
    }

    private static void SaveClientScreenshot(IntPtr window, string output)
    {
        Rect client;
        if (!GetClientRect(window, out client))
            throw new InvalidOperationException("Impossible de lire la zone cliente du jeu.");
        int width = client.Right - client.Left;
        int height = client.Bottom - client.Top;
        if (width < 64 || height < 64)
            throw new InvalidOperationException("Zone cliente du jeu invalide : " + width + "x" + height + ".");
        Point origin = new Point { X = 0, Y = 0 };
        if (!ClientToScreen(window, ref origin))
            throw new InvalidOperationException("Impossible de localiser la zone cliente du jeu.");
        string fullOutput = Path.GetFullPath(output);
        Directory.CreateDirectory(Path.GetDirectoryName(fullOutput));
        using (Bitmap bitmap = new Bitmap(width, height, PixelFormat.Format24bppRgb))
        using (Graphics graphics = Graphics.FromImage(bitmap))
        {
            graphics.CopyFromScreen(origin.X, origin.Y, 0, 0, new Size(width, height), CopyPixelOperation.SourceCopy);
            bitmap.Save(fullOutput, Path.GetExtension(fullOutput).Equals(".jpg", StringComparison.OrdinalIgnoreCase) ? ImageFormat.Jpeg : ImageFormat.Png);
        }
    }

    private static Target GetTarget(Dictionary<string, string> options)
    {
        string state = RequireValue(options, "state");
        if (!File.Exists(state))
            throw new FileNotFoundException("Fichier d'état introuvable.", state);
        Dictionary<string, string> values = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (string line in File.ReadAllLines(state, Encoding.UTF8))
        {
            int equals = line.IndexOf('=');
            if (equals > 0)
                values[line.Substring(0, equals)] = line.Substring(equals + 1);
        }
        int pid;
        if (!values.ContainsKey("pid") || !Int32.TryParse(values["pid"], NumberStyles.Integer, CultureInfo.InvariantCulture, out pid))
            throw new InvalidDataException("PID invalide dans le fichier d'état.");
        if (!values.ContainsKey("game"))
            throw new InvalidDataException("Chemin du jeu absent du fichier d'état.");
        string expected = Path.GetFullPath(values["game"]);
        long rawWindow = 0;
        if (values.ContainsKey("hwnd"))
            Int64.TryParse(values["hwnd"], NumberStyles.Integer, CultureInfo.InvariantCulture, out rawWindow);
        string actual = GetProcessPath(pid);
        RequireSamePath(expected, actual);
        return new Target { Pid = pid, Game = expected, Window = new IntPtr(rawWindow) };
    }

    private static IntPtr ActivateVerifiedWindow(Target target)
    {
        RequireSamePath(target.Game, GetProcessPath(target.Pid));
        IntPtr window = FindTargetWindow(target);
        if (window == IntPtr.Zero)
            throw new InvalidOperationException("La fenêtre du jeu autorisé est introuvable.");
        ShowWindow(window, SwRestore);
        ForceForeground(window);
        for (int i = 0; i < 20 && GetForegroundWindow() != window; i++)
        {
            Thread.Sleep(100);
            ForceForeground(window);
        }
        RequireForeground(window, target.Pid);
        return window;
    }

    private static IntPtr FindTargetWindow(Target target)
    {
        IntPtr window = FindLargestWindow(target.Pid);
        if (window != IntPtr.Zero)
            return window;
        return IsOwnedWindow(target.Window, target.Pid) ? target.Window : IntPtr.Zero;
    }

    private static bool IsOwnedWindow(IntPtr window, int pid)
    {
        if (window == IntPtr.Zero || !IsWindow(window))
            return false;
        uint windowPid;
        GetWindowThreadProcessId(window, out windowPid);
        return windowPid == (uint)pid;
    }

    private static void ForceForeground(IntPtr window)
    {
        if (IsIconic(window)) ShowWindow(window, SwRestore);
        IntPtr foreground = GetForegroundWindow();
        uint ignored;
        uint foregroundThread = foreground == IntPtr.Zero ? 0 : GetWindowThreadProcessId(foreground, out ignored);
        uint currentThread = GetCurrentThreadId();
        bool attached = foregroundThread != 0 && foregroundThread != currentThread &&
            AttachThreadInput(currentThread, foregroundThread, true);
        try
        {
            BringWindowToTop(window);
            SetForegroundWindow(window);
        }
        finally
        {
            if (attached) AttachThreadInput(currentThread, foregroundThread, false);
        }
    }

    private static void RequireForeground(IntPtr expectedWindow, int pid)
    {
        IntPtr foreground = GetForegroundWindow();
        uint foregroundPid;
        GetWindowThreadProcessId(foreground, out foregroundPid);
        if (foreground != expectedWindow || foregroundPid != (uint)pid)
            throw new InvalidOperationException("La fenêtre du jeu autorisé n'est pas au premier plan ; aucune entrée n'a été envoyée.");
    }

    private static IntPtr FindLargestWindow(int pid)
    {
        IntPtr best = IntPtr.Zero;
        long bestArea = 0;
        bool bestVisible = false;
        EnumWindows(delegate(IntPtr window, IntPtr parameter)
        {
            uint windowPid;
            GetWindowThreadProcessId(window, out windowPid);
            if (windowPid != (uint)pid)
                return true;
            Rect rect;
            if (!GetWindowRect(window, out rect))
                return true;
            long area = Math.Max(0, rect.Right - rect.Left) * (long)Math.Max(0, rect.Bottom - rect.Top);
            bool visible = IsWindowVisible(window);
            if (area > 0 && ((visible && !bestVisible) || visible == bestVisible && area > bestArea))
            {
                bestArea = area;
                bestVisible = visible;
                best = window;
            }
            return true;
        }, IntPtr.Zero);
        return best;
    }

    private static string GetProcessPath(int pid)
    {
        IntPtr process = OpenProcess(ProcessQueryLimitedInformation, false, (uint)pid);
        if (process == IntPtr.Zero)
            throw new InvalidOperationException("Le processus autorisé n'existe plus ou son chemin est inaccessible.");
        try
        {
            uint size = 32768;
            StringBuilder path = new StringBuilder((int)size);
            if (!QueryFullProcessImageName(process, 0, path, ref size))
                throw new InvalidOperationException("Impossible de vérifier le chemin de l'exécutable du processus.");
            return Path.GetFullPath(path.ToString());
        }
        finally
        {
            CloseHandle(process);
        }
    }

    private static void RequireSamePath(string expected, string actual)
    {
        if (!String.Equals(Path.GetFullPath(expected), Path.GetFullPath(actual), StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Le PID ne correspond pas au jeu autorisé. Attendu: " + expected + " ; trouvé: " + actual);
    }

    private static void SendKey(ushort vk)
    {
        Input[] input = new Input[2];
        input[0].Type = InputKeyboard;
        input[0].Union.Keyboard.Scan = (ushort)MapVirtualKey(vk, 0);
        input[0].Union.Keyboard.Flags = 0x0008;
        input[1].Type = InputKeyboard;
        input[1].Union.Keyboard.Scan = (ushort)MapVirtualKey(vk, 0);
        input[1].Union.Keyboard.Flags = 0x0008 | KeyeventfKeyup;
        if (SendInput(1, new[] { input[0] }, Marshal.SizeOf(typeof(Input))) != 1)
            throw new InvalidOperationException("La touche n'a pas été envoyée.");
        Thread.Sleep(100);
        if (SendInput(1, new[] { input[1] }, Marshal.SizeOf(typeof(Input))) != 1)
            throw new InvalidOperationException("Le relâchement de la touche n'a pas été envoyé.");
    }

    private static ushort ParseVirtualKey(string name)
    {
        switch (name.Trim().ToUpperInvariant())
        {
            case "ESC": case "ESCAPE": return 0x1B;
            case "ENTER": case "RETURN": return 0x0D;
            case "UP": return 0x26;
            case "DOWN": return 0x28;
            case "LEFT": return 0x25;
            case "RIGHT": return 0x27;
            case "TAB": return 0x09;
            case "SPACE": return 0x20;
            case "HOME": return 0x24;
            case "END": return 0x23;
            case "PAGEUP": return 0x21;
            case "PAGEDOWN": return 0x22;
            default: throw new ArgumentException("Touche non autorisée : " + name);
        }
    }

    private static Dictionary<string, string> ParseOptions(string[] args, int start)
    {
        Dictionary<string, string> result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        for (int i = start; i < args.Length; i++)
        {
            if (!args[i].StartsWith("--", StringComparison.Ordinal) || i + 1 >= args.Length)
                throw new ArgumentException("Option invalide : " + args[i]);
            result[args[i].Substring(2)] = args[++i];
        }
        return result;
    }

    private static string RequireValue(Dictionary<string, string> options, string name)
    {
        string value;
        if (!options.TryGetValue(name, out value) || String.IsNullOrWhiteSpace(value))
            throw new ArgumentException("Option --" + name + " requise.");
        return value;
    }

    private static string RequirePath(Dictionary<string, string> options, string name)
    {
        string path = Path.GetFullPath(RequireValue(options, name));
        if (!File.Exists(path))
            throw new FileNotFoundException("Fichier introuvable.", path);
        return path;
    }

    private static int GetInt(Dictionary<string, string> options, string name, int defaultValue)
    {
        string text;
        int value;
        if (!options.TryGetValue(name, out text))
            return defaultValue;
        if (!Int32.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out value))
            throw new ArgumentException("Valeur entière invalide pour --" + name + ".");
        return value;
    }

    private static int Usage(string message)
    {
        Console.Error.WriteLine(message);
        Console.Error.WriteLine("Usage: launch|info|capture|key|move|relmove|relclick|legacyclick|rellegacyclick|abslegacyclick|sendabsclick|legacyrelmove|legacyrelclick|postclick|cursor|dump|click|close --state <fichier> [options]");
        return 2;
    }

    private sealed class Target
    {
        public int Pid;
        public string Game;
        public IntPtr Window;
    }
}
