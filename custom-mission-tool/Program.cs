using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace HD2CustomMissionManager
{
    internal static class Program
    {
        [DllImport("kernel32.dll")]
        private static extern bool AttachConsole(int processId);

        [STAThread]
        private static int Main(string[] args)
        {
            if (args.Length > 0)
            {
                AttachConsole(-1);
                try
                {
                    string message;
                    if (args[0] == "--check" && args.Length == 2)
                        message = MissionPackageCore.ValidateLibrary(args[1]);
                    else if (args[0] == "--catalogue-test" && args.Length == 4)
                        message = MissionPackageCore.BuildCatalogueForTest(args[1], args[2], args[3]);
                    else if (args[0] == "--integrate" && args.Length == 4)
                        message = MissionPackageCore.Integrate(args[1], args[2], args[3]);
                    else if (args[0] == "--restore" && args.Length == 2)
                        message = MissionPackageCore.Restore(args[1]);
                    else if (args[0] == "--import-user" && args.Length == 5)
                        message = MissionPackageCore.ImportUserMission(
                            args[1], args[2], args[3], args[4]);
                    else if (args[0] == "--detect-language" && args.Length == 2)
                        message = GameLanguageDetector.Detect(args[1]);
                    else if (args[0] == "--self-test-safety" && args.Length == 2)
                        message = MissionPackageCore.RunSafetySelfTests(args[1]);
                    else
                        throw new ArgumentException("Commande de validation inconnue.");
                    SafeConsoleWrite(message, false);
                    return 0;
                }
                catch (Exception error)
                {
                    SafeConsoleWrite("ERREUR : " + error.Message, true);
                    return 2;
                }
            }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SimpleMainForm());
            return 0;
        }

        private static void SafeConsoleWrite(string value, bool error)
        {
            try
            {
                Console.OutputEncoding = Encoding.UTF8;
                if (error) Console.Error.WriteLine(value);
                else Console.WriteLine(value);
            }
            catch (IOException) { }
        }
    }

    internal sealed class MainForm : Form
    {
        private readonly TextBox library = new TextBox();
        private readonly TextBox original = new TextBox();
        private readonly TextBox test = new TextBox();
        private readonly ListView missions = new ListView();
        private readonly Label status = new Label();
        private readonly ProgressBar progress = new ProgressBar();
        private readonly Button create = new Button();
        private readonly Button refresh = new Button();
        private readonly Button verify = new Button();
        private readonly Button integrate = new Button();
        private readonly Button restore = new Button();
        private readonly Button openFolder = new Button();
        private readonly BackgroundWorker worker = new BackgroundWorker();

        public MainForm()
        {
            Text = "H&D2 — Missions personnalisées";
            ClientSize = new Size(860, 590);
            MinimumSize = new Size(760, 520);
            StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9F);

            string basePath = AppDomain.CurrentDomain.BaseDirectory;
            string repositoryLibrary = Path.GetFullPath(Path.Combine(basePath, "..", "custom-missions", "library"));
            string portableLibrary = Path.Combine(basePath, "CustomMissions", "library");
            library.Text = Directory.Exists(repositoryLibrary) ? repositoryLibrary : portableLibrary;
            original.Text = @"D:\Games\Hidden and Dangerous 2";
            test.Text = @"D:\Games\Hidden and Dangerous 2 - Test Menu Personnalise";

            Controls.Add(BuildPathRow("Bibliothèque des missions", library, 18, BrowseLibrary));
            Controls.Add(BuildPathRow("Jeu original (lecture seule)", original, 70, BrowseOriginal));
            Controls.Add(BuildPathRow("Copie de test à préparer", test, 122, BrowseTest));

            missions.Location = new Point(18, 183);
            missions.Size = new Size(824, 265);
            missions.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            missions.View = View.Details;
            missions.FullRowSelect = true;
            missions.GridLines = true;
            missions.Columns.Add("Titre", 275);
            missions.Columns.Add("Catégorie", 190);
            missions.Columns.Add("Dossier", 175);
            missions.Columns.Add("Fichiers", 85);
            Controls.Add(missions);

            int buttonTop = 462;
            create.Text = "Nouvelle mission…";
            create.SetBounds(18, buttonTop, 140, 34);
            create.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            create.Click += CreateClicked;
            openFolder.Text = "Ouvrir le dossier";
            openFolder.SetBounds(166, buttonTop, 130, 34);
            openFolder.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            openFolder.Click += delegate { OpenLibrary(); };
            refresh.Text = "Actualiser";
            refresh.SetBounds(304, buttonTop, 100, 34);
            refresh.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            refresh.Click += delegate { RefreshLibrary(); };
            verify.Text = "Vérifier";
            verify.SetBounds(412, buttonTop, 100, 34);
            verify.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            verify.Click += delegate { VerifyLibrary(); };
            restore.Text = "Restaurer";
            restore.SetBounds(520, buttonTop, 100, 34);
            restore.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            restore.Click += RestoreClicked;
            integrate.Text = "Intégrer dans la copie de test";
            integrate.SetBounds(628, buttonTop, 214, 34);
            integrate.Anchor = AnchorStyles.Bottom | AnchorStyles.Right;
            integrate.Click += IntegrateClicked;
            Controls.AddRange(new Control[] { create, openFolder, refresh, verify, restore, integrate });

            progress.SetBounds(18, 510, 824, 17);
            progress.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            progress.Style = ProgressBarStyle.Marquee;
            progress.Visible = false;
            Controls.Add(progress);
            status.SetBounds(18, 535, 824, 42);
            status.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            status.Text = "Le jeu n'est jamais lancé par cette application.";
            Controls.Add(status);

            worker.DoWork += WorkerDoWork;
            worker.RunWorkerCompleted += WorkerCompleted;
            Shown += delegate { RefreshLibrary(); };
        }

        private Control BuildPathRow(string caption, TextBox field, int top, EventHandler browse)
        {
            Panel panel = new Panel { Left = 18, Top = top, Width = 824, Height = 48,
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };
            Label label = new Label { Text = caption, Left = 0, Top = 0, Width = 260, Height = 18 };
            field.SetBounds(0, 21, 735, 25);
            field.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            Button button = new Button { Text = "Parcourir…", Left = 742, Top = 19, Width = 82, Height = 27,
                Anchor = AnchorStyles.Top | AnchorStyles.Right };
            button.Click += browse;
            panel.Controls.AddRange(new Control[] { label, field, button });
            return panel;
        }

        private void BrowseLibrary(object sender, EventArgs e) { Browse(library, "Choisir la bibliothèque de missions"); }
        private void BrowseOriginal(object sender, EventArgs e) { Browse(original, "Choisir le jeu original"); }
        private void BrowseTest(object sender, EventArgs e) { Browse(test, "Choisir la copie de test"); }

        private void Browse(TextBox field, string description)
        {
            using (FolderBrowserDialog dialog = new FolderBrowserDialog())
            {
                dialog.Description = description;
                if (Directory.Exists(field.Text)) dialog.SelectedPath = field.Text;
                if (dialog.ShowDialog(this) == DialogResult.OK) field.Text = dialog.SelectedPath;
            }
        }

        private void RefreshLibrary()
        {
            try
            {
                MissionLibrary loaded = MissionPackageCore.LoadLibrary(library.Text, false);
                missions.Items.Clear();
                foreach (MissionPackage package in loaded.Packages)
                {
                    ListViewItem item = new ListViewItem(package.Title.ForLanguage("french"));
                    item.SubItems.Add(CategoryLabel(package.Category));
                    item.SubItems.Add(package.MissionDirectory);
                    item.SubItems.Add(package.Files.Count.ToString());
                    missions.Items.Add(item);
                }
                status.Text = loaded.Packages.Count + " mission(s), " + loaded.FileCount
                    + " fichier(s). Le jeu n'a pas été lancé.";
            }
            catch (Exception error) { ShowError(error); }
        }

        private static string CategoryLabel(string category)
        {
            if (category == "multiplayer-adaptation") return "Adaptation multijoueur";
            if (category == "free-exploration") return "Exploration libre / test d'armes";
            return "Mission utilisateur";
        }

        private void VerifyLibrary()
        {
            try
            {
                string message = MissionPackageCore.ValidateLibrary(library.Text);
                status.Text = message + " Le jeu n'a pas été lancé.";
                MessageBox.Show(this, message, "Vérification réussie",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception error) { ShowError(error); }
        }

        private void CreateClicked(object sender, EventArgs e)
        {
            using (NewMissionForm dialog = new NewMissionForm())
            {
                if (dialog.ShowDialog(this) != DialogResult.OK) return;
                try
                {
                    string missionPath = MissionPackageCore.CreatePackage(
                        library.Text, dialog.PackageId, dialog.MissionDirectory,
                        dialog.MissionTitle, dialog.Category);
                    status.Text = "Paquet créé. Copiez maintenant les fichiers de mission, "
                        + "dont tree.klz, dans le dossier ouvert.";
                    Process.Start("explorer.exe", missionPath);
                }
                catch (Exception error) { ShowError(error); }
            }
        }

        private void OpenLibrary()
        {
            try
            {
                Directory.CreateDirectory(library.Text);
                Process.Start("explorer.exe", library.Text);
            }
            catch (Exception error) { ShowError(error); }
        }

        private void IntegrateClicked(object sender, EventArgs e)
        {
            RunWork("integrate");
        }

        private void RestoreClicked(object sender, EventArgs e)
        {
            if (MessageBox.Show(this,
                "Restaurer le catalogue technique et les fichiers remplacés par les paquets ?",
                "Restaurer", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
                RunWork("restore");
        }

        private void RunWork(string operation)
        {
            if (worker.IsBusy) return;
            SetBusy(true);
            worker.RunWorkerAsync(new[] { operation, library.Text, original.Text, test.Text });
        }

        private void WorkerDoWork(object sender, DoWorkEventArgs e)
        {
            string[] arguments = (string[])e.Argument;
            e.Result = arguments[0] == "restore"
                ? MissionPackageCore.Restore(arguments[3])
                : MissionPackageCore.Integrate(arguments[1], arguments[2], arguments[3]);
        }

        private void WorkerCompleted(object sender, RunWorkerCompletedEventArgs e)
        {
            SetBusy(false);
            if (e.Error != null) { ShowError(e.Error); return; }
            status.Text = Convert.ToString(e.Result);
            RefreshLibrary();
            MessageBox.Show(this, Convert.ToString(e.Result), "Terminé",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void SetBusy(bool busy)
        {
            progress.Visible = busy;
            foreach (Control control in new Control[] { create, openFolder, refresh, verify, restore, integrate })
                control.Enabled = !busy;
        }

        private void ShowError(Exception error)
        {
            status.Text = "Erreur : " + error.Message + " Le jeu n'a pas été lancé.";
            MessageBox.Show(this, error.Message, "Impossible de continuer",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    internal sealed class NewMissionForm : Form
    {
        private readonly TextBox id = new TextBox();
        private readonly TextBox directory = new TextBox();
        private readonly TextBox title = new TextBox();
        private readonly ComboBox category = new ComboBox();

        public string PackageId { get { return id.Text; } }
        public string MissionDirectory { get { return directory.Text; } }
        public string MissionTitle { get { return title.Text; } }
        public string Category { get { return Convert.ToString(category.SelectedValue); } }

        public NewMissionForm()
        {
            Text = "Nouvelle mission personnalisée";
            ClientSize = new Size(500, 276);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            StartPosition = FormStartPosition.CenterParent;
            Font = new Font("Segoe UI", 9F);
            AddField("Identifiant unique (ex. auteur.nom-mission)", id, 18);
            AddField("Nom exact du dossier de mission", directory, 76);
            AddField("Titre affiché dans le jeu", title, 134);
            Label categoryLabel = new Label { Text = "Catégorie", Left = 18, Top = 192, Width = 150 };
            category.SetBounds(18, 212, 280, 28);
            category.DropDownStyle = ComboBoxStyle.DropDownList;
            category.DisplayMember = "Text";
            category.ValueMember = "Value";
            category.Items.Add(new Choice("Adaptation multijoueur", "multiplayer-adaptation"));
            category.Items.Add(new Choice("Mission utilisateur", "user-mission"));
            category.Items.Add(new Choice("Exploration libre / test d'armes", "free-exploration"));
            category.SelectedIndex = 1;
            Button ok = new Button { Text = "Créer", Left = 320, Top = 210, Width = 75,
                DialogResult = DialogResult.OK };
            Button cancel = new Button { Text = "Annuler", Left = 405, Top = 210, Width = 75,
                DialogResult = DialogResult.Cancel };
            Controls.AddRange(new Control[] { categoryLabel, category, ok, cancel });
            AcceptButton = ok;
            CancelButton = cancel;
        }

        private void AddField(string label, TextBox field, int top)
        {
            Controls.Add(new Label { Text = label, Left = 18, Top = top, Width = 450 });
            field.SetBounds(18, top + 21, 462, 25);
            Controls.Add(field);
        }

        private sealed class Choice
        {
            public string Text { get; private set; }
            public string Value { get; private set; }
            public Choice(string text, string value) { Text = text; Value = value; }
        }
    }
}
