using System;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Forms;

// Harmless input/capture fixture. No game, process-memory, network or security APIs.
internal sealed class ControlProbe : Form
{
    [DllImport("user32.dll")]
    private static extern bool SetProcessDPIAware();

    private readonly Label clicks = new Label();
    private readonly Label keyboard = new Label();
    private int count;
    private readonly string log = Path.GetFullPath(Path.Combine(
        AppDomain.CurrentDomain.BaseDirectory, "..", "output", "gui-control-probe", "events.log"));

    [STAThread]
    private static void Main()
    {
        SetProcessDPIAware();
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new ControlProbe());
    }

    private ControlProbe()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(log));
        Text = "Vérification du contrôle local — PAS LE JEU";
        ClientSize = new Size(700, 350);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        Font = new Font("Segoe UI", 13);
        BackColor = Color.White;
        KeyPreview = true;
        var title = new Label { Text = "Test de capture, clic et clavier", AutoSize = true,
            Location = new Point(28, 24), Font = new Font("Segoe UI", 19, FontStyle.Bold) };
        var note = new Label { Text = "Cette fenêtre ne lance pas H&D2 et ne modifie aucun réglage.",
            AutoSize = true, Location = new Point(28, 75) };
        clicks.Text = "Clics reçus : 0";
        clicks.SetBounds(28, 125, 630, 35);
        keyboard.Text = "Clavier : en attente de la touche Entrée";
        keyboard.SetBounds(28, 170, 630, 35);
        var test = new Button { Text = "Tester le clic", Location = new Point(28, 240), Size = new Size(285, 60) };
        test.Click += delegate {
            clicks.Text = "Clics reçus : " + (++count);
            clicks.ForeColor = Color.DarkGreen;
            Record("CLICK " + count);
        };
        var close = new Button { Text = "Fermer ce test", Location = new Point(355, 240), Size = new Size(310, 60) };
        close.Click += delegate { Close(); };
        KeyDown += delegate(object sender, KeyEventArgs e) {
            if (e.KeyCode == Keys.Enter) {
                keyboard.Text = "Clavier : touche Entrée reçue";
                keyboard.ForeColor = Color.DarkGreen;
                Record("KEY Enter");
                e.Handled = true;
                e.SuppressKeyPress = true;
            }
        };
        Controls.AddRange(new Control[] { title, note, clicks, keyboard, test, close });
        Shown += delegate { Record("SHOWN"); };
        FormClosed += delegate { Record("CLOSED"); };
        var timeout = new Timer { Interval = 180000 };
        timeout.Tick += delegate { Record("TIMEOUT"); timeout.Stop(); Close(); };
        timeout.Start();
    }

    private void Record(string value)
    {
        File.AppendAllText(log, DateTime.UtcNow.ToString("o") + " " + value + Environment.NewLine);
    }
}
