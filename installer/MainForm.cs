using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace HD2CommunityInstaller
{
    internal sealed class MainForm : Form
    {
        private readonly TextBox gamePath = new TextBox();
        private readonly CheckBox master = new CheckBox();
        private readonly CheckBox directPlay = new CheckBox();
        private readonly CheckBox cmp = new CheckBox();
        private readonly CheckBox soloAdaptations = new CheckBox();
        private readonly CheckBox exploration = new CheckBox();
        private readonly CheckBox objectives = new CheckBox();
        private readonly CheckBox dormant = new CheckBox();
        private readonly CheckBox officialEasterEggs = new CheckBox();
        private readonly CheckBox unlockMissions = new CheckBox();
        private readonly CheckBox graphics = new CheckBox();
        private readonly CheckBox diagnostics = new CheckBox();
        private readonly CheckBox guides = new CheckBox();
        private readonly Button browse = new Button();
        private readonly Button install = new Button();
        private readonly Button restore = new Button();
        private readonly Button verify = new Button();
        private readonly Button openReports = new Button();
        private readonly ProgressBar bar = new ProgressBar();
        private readonly TextBox log = new TextBox();

        public MainForm()
        {
            Text = AppConfig.ProductName + " " + AppConfig.Version;
            ClientSize = new Size(760, 836);
            MinimumSize = new Size(776, 875);
            StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9F);
            BuildLayout();
            gamePath.Text = InstallerCore.DetectGamePath();
            Shown += delegate { RunDiagnostic(); };
        }

        private void BuildLayout()
        {
            Label title = new Label {
                Text = "Hidden & Dangerous 2 - Heritage Pack",
                Font = new Font("Segoe UI Semibold", 18F),
                AutoSize = true, Location = new Point(22, 18)
            };
            Label intro = new Label {
                Text = "Serveurs Internet, missions debloquees, exploration libre et vestiges historiques.",
                AutoSize = true, Location = new Point(25, 58)
            };
            Label pathLabel = new Label {
                Text = "Dossier du jeu :", AutoSize = true, Location = new Point(25, 94)
            };
            gamePath.Location = new Point(25, 116);
            gamePath.Size = new Size(610, 25);
            browse.Text = "Parcourir...";
            browse.Location = new Point(645, 114);
            browse.Size = new Size(90, 28);
            browse.Click += BrowseClick;

            master.Text = "Fusionner la liste du service actuel avec OpenSpy";
            master.Checked = true;
            master.AutoSize = true;
            master.Location = new Point(29, 160);
            directPlay.Text = "Activer le composant Windows DirectPlay si necessaire";
            directPlay.Checked = true;
            directPlay.AutoSize = true;
            directPlay.Location = new Point(29, 188);
            cmp.Text = "Installer ou mettre a jour le CMP officiel (156+ missions cooperatives)";
            cmp.Checked = true;
            cmp.AutoSize = true;
            cmp.Location = new Point(29, 216);
            soloAdaptations.Text = "Installer 11 missions cooperatives adaptees au jeu solo";
            soloAdaptations.Checked = true;
            soloAdaptations.AutoSize = true;
            soloAdaptations.Location = new Point(29, 244);
            exploration.Text = "Autoriser l'exploration hors zone sans message, echec ni mur invisible";
            exploration.Checked = true;
            exploration.AutoSize = true;
            exploration.Location = new Point(29, 272);
            objectives.Text = "Reparer les objectifs optionnels casses ou incoherents";
            objectives.Checked = true;
            objectives.AutoSize = true;
            objectives.Location = new Point(29, 300);
            dormant.Text = "Reactiver guidages, routes et vestiges officiels (experimental)";
            dormant.Checked = true;
            dormant.AutoSize = true;
            dormant.Location = new Point(29, 328);
            officialEasterEggs.Text = "Reactiver les easter eggs neutralises d'Africa 1 et Africa 4 (experimental)";
            officialEasterEggs.Checked = true;
            officialEasterEggs.AutoSize = true;
            officialEasterEggs.Location = new Point(29, 356);
            unlockMissions.Text = "Debloquer toutes les campagnes et missions pour le profil actif";
            unlockMissions.Checked = true;
            unlockMissions.AutoSize = true;
            unlockMissions.Location = new Point(29, 384);
            graphics.Text = "Detecter le PC et appliquer la resolution maximale et les graphismes adaptes";
            graphics.Checked = true;
            graphics.AutoSize = true;
            graphics.Location = new Point(29, 412);
            diagnostics.Text = "Creer automatiquement un rapport local en cas d'erreur du jeu";
            diagnostics.Checked = true;
            diagnostics.AutoSize = true;
            diagnostics.Location = new Point(29, 440);
            guides.Text = "Telecharger les deux guides PDF en "
                + GuideDownloader.LanguageName + " sur le Bureau";
            guides.Checked = true;
            guides.AutoSize = true;
            guides.Location = new Point(29, 468);

            Label safety = new Label {
                Text = "Les fonctions deja actives sont detectees et decochees. Le paquet communautaire "
                    + "est verrouille par SHA-256; les fichiers remplaces sont sauvegardes.",
                AutoSize = false, Size = new Size(706, 42), Location = new Point(28, 502)
            };

            install.Text = "Installer";
            install.Location = new Point(25, 550);
            install.Size = new Size(116, 34);
            install.Click += InstallClick;
            restore.Text = "Restaurer";
            restore.Location = new Point(151, 550);
            restore.Size = new Size(116, 34);
            restore.Click += RestoreClick;
            verify.Text = "Verifier l'etat";
            verify.Location = new Point(277, 550);
            verify.Size = new Size(116, 34);
            verify.Click += delegate { RunDiagnostic(); };
            openReports.Text = "Ouvrir les rapports";
            openReports.Location = new Point(403, 550);
            openReports.Size = new Size(145, 34);
            openReports.Click += OpenReportsClick;

            bar.Location = new Point(25, 598);
            bar.Size = new Size(710, 18);
            log.Location = new Point(25, 628);
            log.Size = new Size(710, 147);
            log.Multiline = true;
            log.ReadOnly = true;
            log.ScrollBars = ScrollBars.Vertical;
            log.Font = new Font("Consolas", 9F);
            log.BackColor = Color.White;

            Label prototypeLabel = new Label {
                Text = "Prototypes dans le jeu : Multijoueur > LAN > Deathmatch (Africa5) "
                    + "ou Occupation (Normandy3 Zone).",
                AutoSize = false, Size = new Size(706, 38), Location = new Point(25, 786)
            };

            Controls.AddRange(new Control[] {
                title, intro, pathLabel, gamePath, browse, master, directPlay, cmp, soloAdaptations,
                exploration, objectives, dormant, officialEasterEggs, unlockMissions, graphics,
                diagnostics, guides, safety, install, restore, verify, openReports, bar, log,
                prototypeLabel
            });
        }


        private void BrowseClick(object sender, EventArgs e)
        {
            using (FolderBrowserDialog dialog = new FolderBrowserDialog())
            {
                dialog.Description = "Selectionnez le dossier de Hidden & Dangerous 2";
                dialog.SelectedPath = gamePath.Text;
                if (dialog.ShowDialog(this) == DialogResult.OK)
                {
                    gamePath.Text = dialog.SelectedPath;
                    RunDiagnostic();
                }
            }
        }

        private async void InstallClick(object sender, EventArgs e)
        {
            if (!InstallerCore.IsGamePath(gamePath.Text))
            {
                MessageBox.Show(this, "Le dossier du jeu n'est pas valide.",
                    AppConfig.ProductName, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            string impact = cmp.Checked
                ? "L'installation telechargera environ 1,08 Go et ajoutera environ 3,6 Go au jeu."
                : "La CMP ne sera pas telechargee.";
            DialogResult answer = MessageBox.Show(
                this, impact + "\r\n\r\nContinuer ?",
                AppConfig.ProductName, MessageBoxButtons.YesNo, MessageBoxIcon.Information);
            if (answer != DialogResult.Yes) return;

            SetBusy(true);
            bar.Value = 0;
            log.Clear();
            bool installed = false;
            InstallOptions options = new InstallOptions {
                GamePath = gamePath.Text,
                ConfigureMasterServer = master.Checked,
                EnableDirectPlay = directPlay.Checked,
                InstallCmp = cmp.Checked,
                InstallSoloAdaptations = soloAdaptations.Checked,
                FreeExploration = exploration.Checked,
                FixOptionalObjectives = objectives.Checked,
                RestoreDormantSequences = dormant.Checked,
                RestoreOfficialEasterEggs = officialEasterEggs.Checked,
                UnlockAllMissions = unlockMissions.Checked,
                AutoConfigureGraphics = graphics.Checked,
                InstallAutomaticDiagnostics = diagnostics.Checked,
                DownloadGuides = guides.Checked
            };
            try
            {
                Progress<string> messages = new Progress<string>(AppendLog);
                Progress<int> percentage = new Progress<int>(
                    delegate(int value) { bar.Value = Math.Max(0, Math.Min(100, value)); });
                Action<string> messageAction = delegate(string value) {
                    ((IProgress<string>)messages).Report(value);
                };
                Action<int> percentAction = delegate(int value) {
                    ((IProgress<int>)percentage).Report(value);
                };
                await Task.Run(delegate {
                    InstallerCore.Install(options, messageAction, percentAction);
                });
                MessageBox.Show(this, "Installation terminee.",
                    AppConfig.ProductName, MessageBoxButtons.OK, MessageBoxIcon.Information);
                installed = true;
            }
            catch (Exception ex)
            {
                AppendLog("ERREUR : " + ex.Message);
                MessageBox.Show(this, ex.Message,
                    AppConfig.ProductName, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally { SetBusy(false); }
            if (installed) RunDiagnostic();
        }

        private async void RestoreClick(object sender, EventArgs e)
        {
            if (!File.Exists(AppConfig.StateFile))
            {
                MessageBox.Show(this, "Aucune installation geree n'est presente.",
                    AppConfig.ProductName, MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            if (MessageBox.Show(this,
                "Restaurer les fichiers sauvegardes et retirer les ajouts de ce pack ?",
                AppConfig.ProductName, MessageBoxButtons.YesNo, MessageBoxIcon.Question)
                != DialogResult.Yes) return;

            SetBusy(true);
            bar.Style = ProgressBarStyle.Marquee;
            try
            {
                Progress<string> messages = new Progress<string>(AppendLog);
                Action<string> messageAction = delegate(string value) {
                    ((IProgress<string>)messages).Report(value);
                };
                await Task.Run(delegate { InstallerCore.Uninstall(messageAction); });
                MessageBox.Show(this, "Restauration terminee.",
                    AppConfig.ProductName, MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                AppendLog("ERREUR : " + ex.Message);
                MessageBox.Show(this, ex.Message,
                    AppConfig.ProductName, MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                bar.Style = ProgressBarStyle.Blocks;
                bar.Value = 0;
                SetBusy(false);
            }
        }

        private async void RunDiagnostic()
        {
            SetBusy(true);
            bar.Style = ProgressBarStyle.Marquee;
            try
            {
                string path = gamePath.Text;
                string result = await Task.Run(delegate {
                    return InstallerCore.BuildDiagnostic(path);
                });
                log.Text = result;
                ApplyDetectedState(result);
            }
            catch (Exception ex) { log.Text = "ERREUR : " + ex.Message; }
            finally
            {
                bar.Style = ProgressBarStyle.Blocks;
                bar.Value = 0;
                SetBusy(false);
            }
        }

        private void OpenReportsClick(object sender, EventArgs e)
        {
            try
            {
                Directory.CreateDirectory(DiagnosticMonitorInstaller.ReportsRoot);
                Process.Start("explorer.exe", DiagnosticMonitorInstaller.ReportsRoot);
            }
            catch (Exception ex)
            {
                MessageBox.Show(this, ex.Message, AppConfig.ProductName,
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void ApplyDetectedState(string diagnostic)
        {
            master.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Fusion des listes Internet :", "deja active");
            directPlay.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "DirectPlay :", "deja actif");
            cmp.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "CMP officiel :", "deja installee");
            soloAdaptations.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Onze adaptations solo :", "deja installees");
            exploration.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Exploration libre :", "deja active");
            objectives.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Objectifs optionnels :", "deja actifs");
            dormant.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Guidages, routes et scripts officiels :", "deja actifs");
            officialEasterEggs.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Easter eggs Africa 1 et Africa 4 :", "deja actifs");
            unlockMissions.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Deblocage des missions :", "deja actif");
            graphics.Checked = !(DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Correctif ecran large :", "deja actif")
                && DiagnosticStatusMatcher.HasStatus(
                    diagnostic, "Graphismes automatiques :", "deja applique"));
            diagnostics.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Rapports automatiques :", "deja actif");
            guides.Checked = !DiagnosticStatusMatcher.HasStatus(
                diagnostic, "Guides PDF sur le Bureau :", "deja presents");
        }
        private void AppendLog(string message)
        {
            if (log.TextLength > 0) log.AppendText(Environment.NewLine);
            log.AppendText(message);
            log.SelectionStart = log.TextLength;
            log.ScrollToCaret();
        }

        private void SetBusy(bool busy)
        {
            install.Enabled = !busy;
            restore.Enabled = !busy;
            verify.Enabled = !busy;
            browse.Enabled = !busy;
            gamePath.Enabled = !busy;
            master.Enabled = !busy;
            directPlay.Enabled = !busy;
            cmp.Enabled = !busy;
            soloAdaptations.Enabled = !busy;
            exploration.Enabled = !busy;
            objectives.Enabled = !busy;
            dormant.Enabled = !busy;
            officialEasterEggs.Enabled = !busy;
            unlockMissions.Enabled = !busy;
            graphics.Enabled = !busy;
            diagnostics.Enabled = !busy;
            guides.Enabled = !busy;
            openReports.Enabled = !busy;
            UseWaitCursor = busy;
        }
    }
}


