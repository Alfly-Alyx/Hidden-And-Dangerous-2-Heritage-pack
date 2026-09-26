using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

namespace HD2CustomMissionManager
{
    internal sealed class SoloMissionPackForm : Form
    {
        private readonly TextBox gamePath = new TextBox();
        private readonly TextBox log = new TextBox();
        private readonly Button browse = new Button();
        private readonly Button install = new Button();
        private readonly Button restore = new Button();
        private readonly Button open = new Button();
        private readonly Label status = new Label();

        public SoloMissionPackForm()
        {
            Text = "H&D2 — Pack de missions solo";
            StartPosition = FormStartPosition.CenterScreen;
            MinimumSize = new Size(720, 480);
            Size = new Size(820, 560);
            Font = new Font("Segoe UI", 9F);

            Label title = new Label {
                Text = "11 adaptations multijoueur vers le mode solo",
                Font = new Font(Font.FontFamily, 15F, FontStyle.Bold),
                AutoSize = true,
                Location = new Point(18, 16)
            };
            Label description = new Label {
                Text = "Alps3 Objectifs, Ardennes1 Objectifs et les neuf missions coopératives officielles.\r\n"
                    + "Les versions multijoueur restent intactes. Les adaptations apparaissent dans Solo > Missions personnalisées > Adaptations multijoueur.",
                AutoSize = false,
                Location = new Point(20, 53),
                Size = new Size(760, 48)
            };
            Label pathLabel = new Label {
                Text = "Dossier de Hidden & Dangerous 2 :",
                AutoSize = true,
                Location = new Point(20, 111)
            };
            gamePath.Location = new Point(20, 134);
            gamePath.Size = new Size(654, 24);
            gamePath.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            gamePath.Text = DetectGamePath();
            gamePath.TextChanged += delegate { RefreshStatus(); };

            browse.Text = "Parcourir…";
            browse.Location = new Point(684, 132);
            browse.Size = new Size(98, 28);
            browse.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            browse.Click += BrowseClick;

            status.Location = new Point(20, 168);
            status.Size = new Size(760, 24);
            status.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;

            install.Text = "Installer / mettre à jour";
            install.Location = new Point(20, 203);
            install.Size = new Size(180, 34);
            install.Click += delegate { Run(false); };

            restore.Text = "Retirer ce pack";
            restore.Location = new Point(210, 203);
            restore.Size = new Size(145, 34);
            restore.Click += delegate { Run(true); };

            open.Text = "Ouvrir CustomMissions";
            open.Location = new Point(365, 203);
            open.Size = new Size(185, 34);
            open.Click += OpenClick;

            log.Location = new Point(20, 250);
            log.Size = new Size(762, 255);
            log.Anchor = AnchorStyles.Top | AnchorStyles.Bottom
                | AnchorStyles.Left | AnchorStyles.Right;
            log.Multiline = true;
            log.ReadOnly = true;
            log.ScrollBars = ScrollBars.Vertical;
            log.BackColor = Color.White;

            Controls.Add(title);
            Controls.Add(description);
            Controls.Add(pathLabel);
            Controls.Add(gamePath);
            Controls.Add(browse);
            Controls.Add(status);
            Controls.Add(install);
            Controls.Add(restore);
            Controls.Add(open);
            Controls.Add(log);
            RefreshStatus();
        }

        private static string DetectGamePath()
        {
            string local = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(
                Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            if (File.Exists(Path.Combine(local, "HD2_SabreSquadron.exe"))) return local;
            string[] registryKeys = {
                @"SOFTWARE\WOW6432Node\GOG.com\Games\1207659052",
                @"SOFTWARE\GOG.com\Games\1207659052"
            };
            foreach (RegistryKey hive in new[] { Registry.LocalMachine, Registry.CurrentUser })
                foreach (string keyName in registryKeys)
                    using (RegistryKey key = hive.OpenSubKey(keyName))
                    {
                        string value = key == null ? null : key.GetValue("path") as string;
                        if (!String.IsNullOrWhiteSpace(value)
                            && File.Exists(Path.Combine(value, "HD2_SabreSquadron.exe")))
                            return value;
                    }
            return "";
        }

        private void BrowseClick(object sender, EventArgs args)
        {
            using (FolderBrowserDialog picker = new FolderBrowserDialog())
            {
                picker.Description = "Choisissez le dossier contenant HD2_SabreSquadron.exe";
                if (Directory.Exists(gamePath.Text)) picker.SelectedPath = gamePath.Text;
                if (picker.ShowDialog(this) == DialogResult.OK)
                    gamePath.Text = picker.SelectedPath;
            }
        }

        private void OpenClick(object sender, EventArgs args)
        {
            try
            {
                string root = Path.GetFullPath(gamePath.Text.Trim());
                string folder = Path.Combine(root, "CustomMissions");
                Directory.CreateDirectory(folder);
                Process.Start("explorer.exe", "\"" + folder + "\"");
            }
            catch (Exception error)
            {
                MessageBox.Show(this, error.Message, "Impossible d'ouvrir le dossier",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void RefreshStatus()
        {
            try
            {
                status.Text = SoloMissionPackBuilder.Check(gamePath.Text.Trim());
                status.ForeColor = Color.DarkGreen;
            }
            catch (Exception error)
            {
                status.Text = error.Message;
                status.ForeColor = Color.DarkRed;
            }
        }

        private void SetBusy(bool busy)
        {
            gamePath.Enabled = !busy;
            browse.Enabled = !busy;
            install.Enabled = !busy;
            restore.Enabled = !busy;
            open.Enabled = !busy;
            UseWaitCursor = busy;
        }

        private void Run(bool remove)
        {
            string root = gamePath.Text.Trim();
            if (remove && MessageBox.Show(this,
                "Retirer uniquement les onze adaptations solo de ce pack ? Les autres missions personnalisées seront conservées.",
                "Retirer le pack", MessageBoxButtons.YesNo, MessageBoxIcon.Question)
                != DialogResult.Yes) return;

            log.Clear();
            SetBusy(true);
            Thread worker = new Thread(delegate()
            {
                try
                {
                    Action<string> progress = delegate(string line) {
                        BeginInvoke((MethodInvoker)delegate {
                            log.AppendText(line + Environment.NewLine);
                        });
                    };
                    string result = remove
                        ? SoloMissionPackBuilder.Restore(root, progress)
                        : SoloMissionPackBuilder.Install(root, progress);
                    BeginInvoke((MethodInvoker)delegate {
                        log.AppendText(result + Environment.NewLine);
                        MessageBox.Show(this, result, "Terminé",
                            MessageBoxButtons.OK, MessageBoxIcon.Information);
                    });
                }
                catch (Exception error)
                {
                    BeginInvoke((MethodInvoker)delegate {
                        log.AppendText("ERREUR : " + error.Message + Environment.NewLine);
                        MessageBox.Show(this, error.Message, "Installation impossible",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
                    });
                }
                finally
                {
                    BeginInvoke((MethodInvoker)delegate {
                        SetBusy(false);
                        RefreshStatus();
                    });
                }
            });
            worker.IsBackground = true;
            worker.SetApartmentState(ApartmentState.STA);
            worker.Start();
        }
    }
}
