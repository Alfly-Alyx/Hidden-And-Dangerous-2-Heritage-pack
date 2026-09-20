using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using Microsoft.Win32;

namespace HD2CustomMissionManager
{
    internal sealed class UiStrings
    {
        private readonly Dictionary<string, string> values =
            new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        public readonly string Code;

        private UiStrings(string code)
        {
            Code = code;
            AddEnglish();
            if (code == "french") AddFrench();
            else if (code == "german") AddGerman();
            else if (code == "italian") AddItalian();
            else if (code == "spanish") AddSpanish();
            else if (code == "czech") AddCzech();
            else if (code == "japan") AddJapanese();
        }

        public string this[string key] { get { return values[key]; } }
        public string Format(string key, params object[] arguments)
        {
            return String.Format(CultureInfo.CurrentCulture, values[key], arguments);
        }

        public static UiStrings Detect(string gameRoot)
        {
            return new UiStrings(GameLanguageDetector.Detect(gameRoot));
        }

        private void AddEnglish()
        {
            values["Title"] = "H&D2 — Custom Missions";
            values["Instruction"] = "Drop each mission folder into CustomMissions, then click Scan and install.";
            values["Folder"] = "Fixed mission folder:";
            values["Language"] = "Detected game language: English";
            values["ColTitle"] = "Title"; values["ColCategory"] = "Category";
            values["ColDirectory"] = "Mission folder"; values["ColFiles"] = "Files";
            values["Import"] = "Add mission…"; values["Add"] = "Add";
            values["ImportPicker"] = "Choose the mission folder (the one containing tree.klz) or its complete package.";
            values["Imported"] = "Mission added to Player-created missions. Click Scan and install to make it available in H&D2.";
            values["New"] = "New mission…"; values["Open"] = "Open folder";
            values["Refresh"] = "Scan"; values["Check"] = "Check";
            values["Restore"] = "Restore"; values["Install"] = "Scan and install";
            values["NeverLaunch"] = "This utility never launches the game.";
            values["Count"] = "{0} mission(s), {1} file(s). The game was not launched.";
            values["Multiplayer"] = "Multiplayer adaptation";
            values["User"] = "User mission";
            values["Explore"] = "Free exploration / weapon test";
            values["CheckOk"] = "The {0} mission(s) are valid.";
            values["CheckTitle"] = "Check successful";
            values["RestoreQuestion"] = "Restore the previous catalogue and the files replaced by mission packages?";
            values["RestoreTitle"] = "Restore"; values["Done"] = "Done";
            values["ErrorTitle"] = "Unable to continue";
            values["Installed"] = "{0} mission(s) installed, {1} file(s) copied. The game was not launched.";
            values["Restored"] = "The previous custom catalogue has been restored. The game was not launched.";
            values["PackageCreated"] = "Package created. Copy the mission files, including tree.klz, into the folder that was opened.";
            values["GameMissing"] = "This utility must be placed in the prepared H&D2 game folder.";
            values["NewTitle"] = "New custom mission";
            values["IdLabel"] = "Unique ID (example: author.mission-name)";
            values["DirectoryLabel"] = "Exact mission folder name";
            values["TitleLabel"] = "Title displayed in the game";
            values["CategoryLabel"] = "Category";
            values["Create"] = "Create"; values["Cancel"] = "Cancel";
        }

        private void AddFrench()
        {
            values["Title"] = "H&D2 — Missions personnalisées";
            values["Instruction"] = "Déposez chaque dossier de mission dans CustomMissions, puis cliquez sur Scanner et installer.";
            values["Folder"] = "Dossier imposé des missions :";
            values["Language"] = "Langue du jeu détectée : français";
            values["ColTitle"] = "Titre"; values["ColCategory"] = "Catégorie";
            values["ColDirectory"] = "Dossier de mission"; values["ColFiles"] = "Fichiers";
            values["Import"] = "Ajouter une mission…"; values["Add"] = "Ajouter";
            values["ImportPicker"] = "Choisissez le dossier de la mission (celui qui contient tree.klz) ou son paquet complet.";
            values["Imported"] = "Mission ajoutée aux missions créées par les joueurs. Cliquez sur Scanner et installer pour la rendre disponible dans H&D2.";
            values["New"] = "Nouvelle mission…"; values["Open"] = "Ouvrir le dossier";
            values["Refresh"] = "Scanner"; values["Check"] = "Vérifier";
            values["Restore"] = "Restaurer"; values["Install"] = "Scanner et installer";
            values["NeverLaunch"] = "Cet utilitaire ne lance jamais le jeu.";
            values["Count"] = "{0} mission(s), {1} fichier(s). Le jeu n'a pas été lancé.";
            values["Multiplayer"] = "Adaptation multijoueur"; values["User"] = "Mission utilisateur";
            values["Explore"] = "Exploration libre / test d'armes";
            values["CheckOk"] = "Les {0} mission(s) sont valides.";
            values["CheckTitle"] = "Vérification réussie";
            values["RestoreQuestion"] = "Restaurer le catalogue précédent et les fichiers remplacés par les paquets ?";
            values["RestoreTitle"] = "Restaurer"; values["Done"] = "Terminé";
            values["ErrorTitle"] = "Impossible de continuer";
            values["Installed"] = "{0} mission(s) installée(s), {1} fichier(s) copié(s). Le jeu n'a pas été lancé.";
            values["Restored"] = "Le catalogue personnalisé précédent a été restauré. Le jeu n'a pas été lancé.";
            values["PackageCreated"] = "Paquet créé. Copiez les fichiers de mission, dont tree.klz, dans le dossier ouvert.";
            values["GameMissing"] = "Cet utilitaire doit être placé dans le dossier préparé de H&D2.";
            values["NewTitle"] = "Nouvelle mission personnalisée";
            values["IdLabel"] = "Identifiant unique (exemple : auteur.nom-mission)";
            values["DirectoryLabel"] = "Nom exact du dossier de mission";
            values["TitleLabel"] = "Titre affiché dans le jeu"; values["CategoryLabel"] = "Catégorie";
            values["Create"] = "Créer"; values["Cancel"] = "Annuler";
        }

        private void AddGerman()
        {
            values["Title"] = "H&D2 — Eigene Missionen";
            values["Instruction"] = "Legen Sie jeden Missionsordner in CustomMissions ab. Klicken Sie auf Suchen und installieren.";
            values["Folder"] = "Fester Missionsordner:"; values["Language"] = "Erkannte Spielsprache: Deutsch";
            values["ColTitle"] = "Titel"; values["ColCategory"] = "Kategorie";
            values["ColDirectory"] = "Missionsordner"; values["ColFiles"] = "Dateien";
            values["Import"] = "Mission hinzufügen…"; values["Add"] = "Hinzufügen";
            values["ImportPicker"] = "Wählen Sie den Missionsordner mit tree.klz oder das vollständige Paket.";
            values["Imported"] = "Mission zu den von Spielern erstellten Missionen hinzugefügt. Klicken Sie auf Suchen und installieren.";
            values["New"] = "Neue Mission…"; values["Open"] = "Ordner öffnen";
            values["Refresh"] = "Suchen"; values["Check"] = "Prüfen";
            values["Restore"] = "Wiederherstellen"; values["Install"] = "Suchen und installieren";
            values["NeverLaunch"] = "Dieses Programm startet das Spiel niemals.";
            values["Multiplayer"] = "Mehrspieler-Anpassung"; values["User"] = "Benutzermission";
            values["Explore"] = "Freie Erkundung / Waffentest";
            values["Count"] = "{0} Mission(en), {1} Datei(en). Das Spiel wurde nicht gestartet.";
            values["CheckOk"] = "{0} Mission(en) ist/sind gültig.";
            values["CheckTitle"] = "Prüfung erfolgreich";
            values["RestoreQuestion"] = "Vorherigen Katalog und ersetzte Dateien wiederherstellen?";
            values["RestoreTitle"] = "Wiederherstellen"; values["Done"] = "Fertig";
            values["ErrorTitle"] = "Fortfahren nicht möglich";
            values["Installed"] = "{0} Mission(en) installiert, {1} Datei(en) kopiert. Das Spiel wurde nicht gestartet.";
            values["Restored"] = "Der vorherige Katalog wurde wiederhergestellt. Das Spiel wurde nicht gestartet.";
            values["PackageCreated"] = "Paket erstellt. Kopieren Sie die Missionsdateien einschließlich tree.klz in den geöffneten Ordner.";
            values["GameMissing"] = "Dieses Programm muss sich im vorbereiteten H&D2-Spielordner befinden.";
            values["NewTitle"] = "Neue eigene Mission"; values["IdLabel"] = "Eindeutige ID (Beispiel: autor.missionsname)";
            values["DirectoryLabel"] = "Genauer Name des Missionsordners";
            values["TitleLabel"] = "Im Spiel angezeigter Titel"; values["CategoryLabel"] = "Kategorie";
            values["Create"] = "Erstellen"; values["Cancel"] = "Abbrechen";
        }

        private void AddItalian()
        {
            values["Title"] = "H&D2 — Missioni personalizzate";
            values["Instruction"] = "Metti ogni cartella missione in CustomMissions, poi fai clic su Cerca e installa.";
            values["Folder"] = "Cartella fissa delle missioni:"; values["Language"] = "Lingua del gioco rilevata: italiano";
            values["ColTitle"] = "Titolo"; values["ColCategory"] = "Categoria";
            values["ColDirectory"] = "Cartella missione"; values["ColFiles"] = "File";
            values["Import"] = "Aggiungi missione…"; values["Add"] = "Aggiungi";
            values["ImportPicker"] = "Scegli la cartella della missione con tree.klz o il pacchetto completo.";
            values["Imported"] = "Missione aggiunta alle missioni create dai giocatori. Fai clic su Cerca e installa.";
            values["New"] = "Nuova missione…"; values["Open"] = "Apri cartella";
            values["Refresh"] = "Cerca"; values["Check"] = "Verifica";
            values["Restore"] = "Ripristina"; values["Install"] = "Cerca e installa";
            values["NeverLaunch"] = "Questa utilità non avvia mai il gioco.";
            values["Multiplayer"] = "Adattamento multigiocatore"; values["User"] = "Missione utente";
            values["Explore"] = "Esplorazione libera / test armi";
            values["Count"] = "{0} missione/i, {1} file. Il gioco non è stato avviato.";
            values["CheckOk"] = "Le missioni valide sono {0}."; values["CheckTitle"] = "Verifica riuscita";
            values["RestoreQuestion"] = "Ripristinare il catalogo precedente e i file sostituiti?";
            values["RestoreTitle"] = "Ripristina"; values["Done"] = "Operazione completata";
            values["ErrorTitle"] = "Impossibile continuare";
            values["Installed"] = "{0} missione/i installate, {1} file copiati. Il gioco non è stato avviato.";
            values["Restored"] = "Il catalogo precedente è stato ripristinato. Il gioco non è stato avviato.";
            values["PackageCreated"] = "Pacchetto creato. Copia i file della missione, incluso tree.klz, nella cartella aperta.";
            values["GameMissing"] = "Questa utilità deve trovarsi nella cartella preparata di H&D2.";
            values["NewTitle"] = "Nuova missione personalizzata"; values["IdLabel"] = "ID univoco (esempio: autore.nome-missione)";
            values["DirectoryLabel"] = "Nome esatto della cartella della missione";
            values["TitleLabel"] = "Titolo visualizzato nel gioco"; values["CategoryLabel"] = "Categoria";
            values["Create"] = "Crea"; values["Cancel"] = "Annulla";
        }

        private void AddSpanish()
        {
            values["Title"] = "H&D2 — Misiones personalizadas";
            values["Instruction"] = "Coloca cada carpeta de misión en CustomMissions y pulsa Buscar e instalar.";
            values["Folder"] = "Carpeta fija de misiones:"; values["Language"] = "Idioma del juego detectado: español";
            values["ColTitle"] = "Título"; values["ColCategory"] = "Categoría";
            values["ColDirectory"] = "Carpeta de misión"; values["ColFiles"] = "Archivos";
            values["Import"] = "Añadir misión…"; values["Add"] = "Añadir";
            values["ImportPicker"] = "Elige la carpeta de la misión con tree.klz o su paquete completo.";
            values["Imported"] = "Misión añadida a las misiones creadas por jugadores. Pulsa Buscar e instalar.";
            values["New"] = "Nueva misión…"; values["Open"] = "Abrir carpeta";
            values["Refresh"] = "Buscar"; values["Check"] = "Verificar";
            values["Restore"] = "Restaurar"; values["Install"] = "Buscar e instalar";
            values["NeverLaunch"] = "Esta utilidad nunca inicia el juego.";
            values["Multiplayer"] = "Adaptación multijugador"; values["User"] = "Misión de usuario";
            values["Explore"] = "Exploración libre / prueba de armas";
            values["Count"] = "{0} misión(es), {1} archivo(s). El juego no se ha iniciado.";
            values["CheckOk"] = "Las {0} misión(es) son válidas."; values["CheckTitle"] = "Verificación correcta";
            values["RestoreQuestion"] = "¿Restaurar el catálogo anterior y los archivos reemplazados?";
            values["RestoreTitle"] = "Restaurar"; values["Done"] = "Terminado";
            values["ErrorTitle"] = "No se puede continuar";
            values["Installed"] = "{0} misión(es) instaladas, {1} archivo(s) copiados. El juego no se ha iniciado.";
            values["Restored"] = "Se ha restaurado el catálogo anterior. El juego no se ha iniciado.";
            values["PackageCreated"] = "Paquete creado. Copia los archivos de la misión, incluido tree.klz, en la carpeta abierta.";
            values["GameMissing"] = "Esta utilidad debe estar en la carpeta preparada de H&D2.";
            values["NewTitle"] = "Nueva misión personalizada"; values["IdLabel"] = "ID único (ejemplo: autor.nombre-mision)";
            values["DirectoryLabel"] = "Nombre exacto de la carpeta de misión";
            values["TitleLabel"] = "Título mostrado en el juego"; values["CategoryLabel"] = "Categoría";
            values["Create"] = "Crear"; values["Cancel"] = "Cancelar";
        }

        private void AddCzech()
        {
            values["Title"] = "H&D2 — Vlastní mise";
            values["Instruction"] = "Vložte každou složku mise do CustomMissions a klikněte na Najít a instalovat.";
            values["Folder"] = "Pevná složka misí:"; values["Language"] = "Zjištěný jazyk hry: čeština";
            values["ColTitle"] = "Název"; values["ColCategory"] = "Kategorie";
            values["ColDirectory"] = "Složka mise"; values["ColFiles"] = "Soubory";
            values["Import"] = "Přidat misi…"; values["Add"] = "Přidat";
            values["ImportPicker"] = "Vyberte složku mise obsahující tree.klz nebo celý balíček.";
            values["Imported"] = "Mise byla přidána mezi mise vytvořené hráči. Klikněte na Najít a instalovat.";
            values["New"] = "Nová mise…"; values["Open"] = "Otevřít složku";
            values["Refresh"] = "Najít"; values["Check"] = "Zkontrolovat";
            values["Restore"] = "Obnovit zpět"; values["Install"] = "Najít a instalovat";
            values["NeverLaunch"] = "Tento nástroj nikdy nespouští hru.";
            values["Multiplayer"] = "Úprava pro více hráčů"; values["User"] = "Uživatelská mise";
            values["Explore"] = "Volný průzkum / test zbraní";
            values["Count"] = "Počet misí: {0}, souborů: {1}. Hra nebyla spuštěna.";
            values["CheckOk"] = "Počet platných misí: {0}."; values["CheckTitle"] = "Kontrola proběhla úspěšně";
            values["RestoreQuestion"] = "Obnovit předchozí katalog a nahrazené soubory?";
            values["RestoreTitle"] = "Obnovit"; values["Done"] = "Hotovo";
            values["ErrorTitle"] = "Nelze pokračovat";
            values["Installed"] = "Nainstalované mise: {0}, zkopírované soubory: {1}. Hra nebyla spuštěna.";
            values["Restored"] = "Předchozí katalog byl obnoven. Hra nebyla spuštěna.";
            values["PackageCreated"] = "Balíček byl vytvořen. Do otevřené složky zkopírujte soubory mise včetně tree.klz.";
            values["GameMissing"] = "Tento nástroj musí být v připravené složce hry H&D2.";
            values["NewTitle"] = "Nová vlastní mise"; values["IdLabel"] = "Jedinečné ID (příklad: autor.nazev-mise)";
            values["DirectoryLabel"] = "Přesný název složky mise";
            values["TitleLabel"] = "Název zobrazený ve hře"; values["CategoryLabel"] = "Kategorie";
            values["Create"] = "Vytvořit"; values["Cancel"] = "Zrušit";
        }

        private void AddJapanese()
        {
            values["Title"] = "H&D2 — カスタムミッション";
            values["Instruction"] = "各ミッションのフォルダーを CustomMissions に入れ、「スキャンしてインストール」を押してください。";
            values["Folder"] = "固定ミッションフォルダー:"; values["Language"] = "検出されたゲーム言語: 日本語";
            values["ColTitle"] = "タイトル"; values["ColCategory"] = "カテゴリ";
            values["ColDirectory"] = "ミッションフォルダー"; values["ColFiles"] = "ファイル";
            values["Import"] = "ミッションを追加…"; values["Add"] = "追加";
            values["ImportPicker"] = "tree.klz を含むミッションフォルダー、または完全なパックを選択してください。";
            values["Imported"] = "プレイヤー作成ミッションに追加しました。「スキャンしてインストール」を押してください。";
            values["New"] = "新しいミッション…"; values["Open"] = "フォルダーを開く";
            values["Refresh"] = "スキャン"; values["Check"] = "確認";
            values["Restore"] = "復元"; values["Install"] = "スキャンしてインストール";
            values["NeverLaunch"] = "このツールはゲームを起動しません。";
            values["Multiplayer"] = "マルチプレイ改作"; values["User"] = "ユーザーミッション";
            values["Explore"] = "フリー探索 / 武器テスト";
            values["Count"] = "ミッション {0} 件、ファイル {1} 件。ゲームは起動されていません。";
            values["CheckOk"] = "{0} 件のミッションは有効です。"; values["CheckTitle"] = "確認完了";
            values["RestoreQuestion"] = "以前のカタログと置換されたファイルを復元しますか？";
            values["RestoreTitle"] = "復元"; values["Done"] = "完了";
            values["ErrorTitle"] = "続行できません";
            values["Installed"] = "ミッション {0} 件をインストールし、ファイル {1} 件をコピーしました。ゲームは起動されていません。";
            values["Restored"] = "以前のカタログを復元しました。ゲームは起動されていません。";
            values["PackageCreated"] = "パックを作成しました。tree.klz を含むミッションファイルを開いたフォルダーにコピーしてください。";
            values["GameMissing"] = "このツールを準備済みの H&D2 ゲームフォルダーに置いてください。";
            values["NewTitle"] = "新しいカスタムミッション"; values["IdLabel"] = "一意の ID（例: author.mission-name）";
            values["DirectoryLabel"] = "ミッションフォルダーの正確な名前";
            values["TitleLabel"] = "ゲーム内に表示するタイトル"; values["CategoryLabel"] = "カテゴリ";
            values["Create"] = "作成"; values["Cancel"] = "キャンセル";
        }
    }

    internal static class GameLanguageDetector
    {
        public static string Detect(string gameRoot)
        {
            string value = RegistryLanguage();
            if (String.IsNullOrWhiteSpace(value)) value = GogLanguage(gameRoot);
            if (String.IsNullOrWhiteSpace(value)) value = ArchiveLanguage(gameRoot);
            if (String.IsNullOrWhiteSpace(value)) value = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName;
            value = value.ToLowerInvariant();
            if (value.Contains("french") || value == "fr") return "french";
            if (value.Contains("german") || value == "de") return "german";
            if (value.Contains("italian") || value == "it") return "italian";
            if (value.Contains("spanish") || value == "es") return "spanish";
            if (value.Contains("czech") || value == "cs") return "czech";
            if (value.Contains("japan") || value == "ja") return "japan";
            return "english";
        }

        private static string RegistryLanguage()
        {
            foreach (RegistryView view in new[] { RegistryView.Registry32, RegistryView.Registry64 })
                try
                {
                    using (RegistryKey machine = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, view))
                    using (RegistryKey key = machine.OpenSubKey(@"SOFTWARE\Illusion Softworks\Hidden & Dangerous 2"))
                        if (key != null)
                        {
                            object value = key.GetValue("language");
                            if (value != null) return Convert.ToString(value);
                        }
                }
                catch { }
            return null;
        }

        private static string GogLanguage(string gameRoot)
        {
            try
            {
                string[] files = Directory.GetFiles(gameRoot, "goggame-*.info");
                if (files.Length == 0) return null;
                Match match = Regex.Match(File.ReadAllText(files[0]),
                    "\\\"language\\\"\\s*:\\s*\\\"([^\\\"]+)\\\"", RegexOptions.IgnoreCase);
                return match.Success ? match.Groups[1].Value : null;
            }
            catch { return null; }
        }

        private static string ArchiveLanguage(string gameRoot)
        {
            try
            {
                string[] files = Directory.GetFiles(gameRoot, "Lang*.dta");
                return files.Length == 1 ? Path.GetFileNameWithoutExtension(files[0]).Substring(4) : null;
            }
            catch { return null; }
        }
    }

    internal sealed class SimpleMainForm : Form
    {
        private readonly string gameRoot;
        private readonly string missionRoot;
        private readonly UiStrings text;
        private readonly ListView missions = new ListView();
        private readonly Label status = new Label();
        private readonly ProgressBar progress = new ProgressBar();
        private readonly Button import = new Button();
        private readonly Button create = new Button();
        private readonly Button open = new Button();
        private readonly Button refresh = new Button();
        private readonly Button check = new Button();
        private readonly Button restore = new Button();
        private readonly Button install = new Button();
        private readonly BackgroundWorker worker = new BackgroundWorker();

        public SimpleMainForm()
        {
            gameRoot = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(
                Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            missionRoot = Path.Combine(gameRoot, "CustomMissions");
            text = UiStrings.Detect(gameRoot);
            Text = text["Title"];
            ClientSize = new Size(920, 500);
            MinimumSize = new Size(840, 440);
            StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9F);

            Label instruction = new Label { Left = 18, Top = 16, Width = 884, Height = 20,
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right,
                Text = text["Instruction"] };
            Label folder = new Label { Left = 18, Top = 43, Width = 884, Height = 38,
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right,
                Text = text["Folder"] + " " + missionRoot + Environment.NewLine + text["Language"] };
            Controls.Add(instruction); Controls.Add(folder);

            missions.SetBounds(18, 88, 884, 292);
            missions.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            missions.View = View.Details; missions.FullRowSelect = true; missions.GridLines = true;
            missions.Columns.Add(text["ColTitle"], 300);
            missions.Columns.Add(text["ColCategory"], 225);
            missions.Columns.Add(text["ColDirectory"], 230);
            missions.Columns.Add(text["ColFiles"], 75);
            Controls.Add(missions);

            int top = 393;
            ConfigureButton(import, text["Import"], 18, top, 145, ImportClicked);
            ConfigureButton(create, text["New"], 171, top, 120, CreateClicked);
            ConfigureButton(open, text["Open"], 299, top, 115, delegate { OpenFolder(); });
            ConfigureButton(refresh, text["Refresh"], 422, top, 88, delegate { RefreshLibrary(); });
            ConfigureButton(check, text["Check"], 518, top, 88, delegate { CheckLibrary(); });
            ConfigureButton(restore, text["Restore"], 614, top, 92, RestoreClicked);
            ConfigureButton(install, text["Install"], 714, top, 188, delegate { RunWork("install"); });
            install.Anchor = AnchorStyles.Bottom | AnchorStyles.Right;

            progress.SetBounds(18, 439, 884, 16);
            progress.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            progress.Style = ProgressBarStyle.Marquee; progress.Visible = false;
            status.SetBounds(18, 463, 884, 28);
            status.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            status.Text = text["NeverLaunch"];
            Controls.Add(progress); Controls.Add(status);
            worker.DoWork += Work; worker.RunWorkerCompleted += WorkCompleted;
            Shown += delegate { InitializeLibrary(); };
        }

        private void ConfigureButton(Button button, string caption, int left, int top, int width, EventHandler click)
        {
            button.Text = caption; button.SetBounds(left, top, width, 34);
            button.Anchor = AnchorStyles.Bottom | AnchorStyles.Left; button.Click += click;
            Controls.Add(button);
        }

        private bool GameIsPrepared()
        {
            return File.Exists(Path.Combine(gameRoot, "HD2_SabreSquadron.exe"))
                && File.Exists(Path.Combine(gameRoot, "SabreSquadron.dta"));
        }

        private void InitializeLibrary()
        {
            Directory.CreateDirectory(missionRoot);
            if (!GameIsPrepared())
            {
                install.Enabled = restore.Enabled = false;
                status.Text = text["GameMissing"];
            }
            RefreshLibrary();
        }

        private void RefreshLibrary()
        {
            try
            {
                MissionLibrary loaded = MissionPackageCore.LoadLibrary(missionRoot, false);
                missions.Items.Clear();
                foreach (MissionPackage package in loaded.Packages)
                {
                    ListViewItem item = new ListViewItem(package.Title.ForLanguage(text.Code));
                    item.SubItems.Add(Category(package.Category));
                    item.SubItems.Add(package.MissionDirectory);
                    item.SubItems.Add(package.Files.Count.ToString(CultureInfo.CurrentCulture));
                    missions.Items.Add(item);
                }
                status.Text = text.Format("Count", loaded.Packages.Count, loaded.FileCount);
            }
            catch (Exception error) { ShowError(error); }
        }

        private string Category(string category)
        {
            if (category == "multiplayer-adaptation") return text["Multiplayer"];
            if (category == "free-exploration") return text["Explore"];
            return text["User"];
        }

        private void CheckLibrary()
        {
            try
            {
                MissionLibrary loaded = MissionPackageCore.LoadLibrary(missionRoot, false);
                string message = text.Format("CheckOk", loaded.Packages.Count);
                status.Text = message + " " + text["NeverLaunch"];
                MessageBox.Show(this, message, text["CheckTitle"],
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception error) { ShowError(error); }
        }

        private void OpenFolder()
        {
            try { Directory.CreateDirectory(missionRoot); Process.Start("explorer.exe", missionRoot); }
            catch (Exception error) { ShowError(error); }
        }

        private void ImportClicked(object sender, EventArgs e)
        {
            using (FolderBrowserDialog picker = new FolderBrowserDialog())
            {
                picker.Description = text["ImportPicker"];
                picker.ShowNewFolderButton = false;
                if (picker.ShowDialog(this) != DialogResult.OK) return;
                string defaultTitle = new DirectoryInfo(picker.SelectedPath).Name;
                using (ImportMissionForm dialog = new ImportMissionForm(text, defaultTitle))
                {
                    if (dialog.ShowDialog(this) != DialogResult.OK) return;
                    try
                    {
                        MissionPackageCore.ImportUserMission(picker.SelectedPath, missionRoot,
                            dialog.MissionTitle, text.Code);
                        RefreshLibrary();
                        status.Text = text["Imported"];
                        MessageBox.Show(this, text["Imported"], text["Done"],
                            MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception error) { ShowError(error); }
                }
            }
        }

        private void CreateClicked(object sender, EventArgs e)
        {
            using (SimpleNewMissionForm dialog = new SimpleNewMissionForm(text))
            {
                if (dialog.ShowDialog(this) != DialogResult.OK) return;
                try
                {
                    string path = MissionPackageCore.CreatePackage(missionRoot,
                        dialog.PackageId, dialog.MissionDirectory, dialog.MissionTitle,
                        dialog.Category, text.Code);
                    status.Text = text["PackageCreated"];
                    Process.Start("explorer.exe", path);
                }
                catch (Exception error) { ShowError(error); }
            }
        }

        private void RestoreClicked(object sender, EventArgs e)
        {
            if (MessageBox.Show(this, text["RestoreQuestion"], text["RestoreTitle"],
                MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes) RunWork("restore");
        }

        private void RunWork(string operation)
        {
            if (worker.IsBusy) return;
            // Integrate rescans the fixed library, including folders dropped
            // after this window was opened; no manual import step is required.
            SetBusy(true); worker.RunWorkerAsync(operation);
        }

        private void Work(object sender, DoWorkEventArgs e)
        {
            if (Convert.ToString(e.Argument) == "restore")
            {
                e.Result = MissionPackageCore.Restore(gameRoot);
            }
            else
            {
                e.Result = MissionPackageCore.Integrate(
                    missionRoot, gameRoot, gameRoot);
            }
        }

        private void WorkCompleted(object sender, RunWorkerCompletedEventArgs e)
        {
            SetBusy(false);
            if (e.Error != null) { ShowError(e.Error); return; }
            RefreshLibrary();
            status.Text = Convert.ToString(e.Result);
            MessageBox.Show(this, Convert.ToString(e.Result), text["Done"],
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void SetBusy(bool busy)
        {
            progress.Visible = busy;
            foreach (Control control in new Control[] { import, create, open, refresh, check, restore, install })
                control.Enabled = !busy;
        }

        private void ShowError(Exception error)
        {
            status.Text = text["ErrorTitle"] + ": " + error.Message + " " + text["NeverLaunch"];
            MessageBox.Show(this, error.Message, text["ErrorTitle"],
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    internal sealed class ImportMissionForm : Form
    {
        private readonly TextBox title = new TextBox();
        public string MissionTitle { get { return title.Text; } }

        public ImportMissionForm(UiStrings text, string defaultTitle)
        {
            Text = text["Import"];
            ClientSize = new Size(500, 132);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false; MinimizeBox = false;
            StartPosition = FormStartPosition.CenterParent;
            Font = new Font("Segoe UI", 9F);
            Controls.Add(new Label { Text = text["TitleLabel"], Left = 18, Top = 18, Width = 450 });
            title.SetBounds(18, 42, 462, 25);
            title.Text = defaultTitle;
            title.SelectAll();
            Button add = new Button { Text = text["Add"], Left = 320, Top = 86, Width = 75,
                DialogResult = DialogResult.OK };
            Button cancel = new Button { Text = text["Cancel"], Left = 405, Top = 86, Width = 75,
                DialogResult = DialogResult.Cancel };
            Controls.AddRange(new Control[] { title, add, cancel });
            AcceptButton = add; CancelButton = cancel;
        }
    }

    internal sealed class SimpleNewMissionForm : Form
    {
        private readonly TextBox id = new TextBox();
        private readonly TextBox directory = new TextBox();
        private readonly TextBox title = new TextBox();
        private readonly ComboBox category = new ComboBox();
        public string PackageId { get { return id.Text; } }
        public string MissionDirectory { get { return directory.Text; } }
        public string MissionTitle { get { return title.Text; } }
        public string Category { get { return Convert.ToString(category.SelectedValue); } }

        public SimpleNewMissionForm(UiStrings text)
        {
            Text = text["NewTitle"]; ClientSize = new Size(500, 276);
            FormBorderStyle = FormBorderStyle.FixedDialog; MaximizeBox = false; MinimizeBox = false;
            StartPosition = FormStartPosition.CenterParent; Font = new Font("Segoe UI", 9F);
            AddField(text["IdLabel"], id, 18); AddField(text["DirectoryLabel"], directory, 76);
            AddField(text["TitleLabel"], title, 134);
            Controls.Add(new Label { Text = text["CategoryLabel"], Left = 18, Top = 192, Width = 180 });
            category.SetBounds(18, 212, 280, 28); category.DropDownStyle = ComboBoxStyle.DropDownList;
            category.DisplayMember = "Text"; category.ValueMember = "Value";
            category.Items.Add(new Choice(text["Multiplayer"], "multiplayer-adaptation"));
            category.Items.Add(new Choice(text["User"], "user-mission"));
            category.Items.Add(new Choice(text["Explore"], "free-exploration")); category.SelectedIndex = 1;
            Button ok = new Button { Text = text["Create"], Left = 320, Top = 210, Width = 75,
                DialogResult = DialogResult.OK };
            Button cancel = new Button { Text = text["Cancel"], Left = 405, Top = 210, Width = 75,
                DialogResult = DialogResult.Cancel };
            Controls.AddRange(new Control[] { category, ok, cancel }); AcceptButton = ok; CancelButton = cancel;
        }

        private void AddField(string label, TextBox field, int top)
        {
            Controls.Add(new Label { Text = label, Left = 18, Top = top, Width = 450 });
            field.SetBounds(18, top + 21, 462, 25); Controls.Add(field);
        }

        private sealed class Choice
        {
            public string Text { get; private set; } public string Value { get; private set; }
            public Choice(string text, string value) { Text = text; Value = value; }
        }
    }
}
