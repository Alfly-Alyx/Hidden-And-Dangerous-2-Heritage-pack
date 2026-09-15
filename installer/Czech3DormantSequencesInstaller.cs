using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Czech3DormantSequencesInstaller
    {
        private const string TruckPath = "Scripts/CZECH3/opel_driver.scr";
        private const string MechanicPath =
            "Scripts/CZECH3/R_cz3_pila_kladivo.scr";
        private const string RadioOperatorPath = "Scripts/CZECH3/Radista.scr";
        private const string RegistryPath = "Missions/CZECH3/Scripts.dta";
        private const string CheckpointPath = "Missions/CZECH3/check2.bin";
        private const string ScenePath = "Missions/CZECH3/scene2.bin";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] truck = ReadSource(ResolveSource(
                gamePath, TruckPath, ScriptArchives));
            byte[] patchedTruck = PatchTruck(truck);
            if (BytesEqual(truck, patchedTruck))
                throw new InvalidDataException(
                    "Le stationnement complet du camion Czech 3 semble deja actif.");
            ValidateTruck(patchedTruck);
            if (!BytesEqual(patchedTruck, PatchTruck(patchedTruck)))
                throw new InvalidDataException(
                    "La restauration du camion Czech 3 n'est pas idempotente.");

            byte[] mechanic = ReadSource(ResolveSource(
                gamePath, MechanicPath, ScriptArchives));
            byte[] patchedMechanic = PatchMechanic(mechanic);
            if (BytesEqual(mechanic, patchedMechanic))
                throw new InvalidDataException(
                    "L'arret du dialogue du mecanicien Czech 3 semble deja actif.");
            ValidateMechanic(patchedMechanic);
            if (!BytesEqual(patchedMechanic, PatchMechanic(patchedMechanic)))
                throw new InvalidDataException(
                    "La restauration du mecanicien Czech 3 n'est pas idempotente.");

            byte[] radioOperator = ReadSource(ResolveSource(
                gamePath, RadioOperatorPath, ScriptArchives));
            byte[] patchedRadioOperator = PatchRadioOperator(radioOperator);
            if (BytesEqual(radioOperator, patchedRadioOperator))
                throw new InvalidDataException(
                    "Le poste de precision du radio-operateur Czech 3 semble deja actif.");
            ValidateRadioOperator(patchedRadioOperator);
            if (!BytesEqual(patchedRadioOperator, PatchRadioOperator(patchedRadioOperator)))
                throw new InvalidDataException(
                    "La restauration du radio-operateur Czech 3 n'est pas idempotente.");

            ValidateAssets(gamePath);
            return "Czech 3 verifie : le stationnement complet du camion et "
                + "l'arret du dialogue du mecanicien mort et le poste de "
                + "precision du radio-operateur peuvent reutiliser leurs "
                + "instructions officielles.";
        }

        public static bool IsTruckActive(string gamePath)
        {
            return IsTargetActive(gamePath, TruckPath, ValidateTruck);
        }

        public static bool IsMechanicActive(string gamePath)
        {
            return IsTargetActive(gamePath, MechanicPath, ValidateMechanic);
        }

        public static bool IsRadioOperatorActive(string gamePath)
        {
            return IsTargetActive(
                gamePath, RadioOperatorPath, ValidateRadioOperator);
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            ValidateAssets(gamePath);
            InstallOne(gamePath, TruckPath, PatchTruck, ValidateTruck,
                journal, prepared, progress,
                "Restauration du stationnement complet du camion Czech 3...",
                "Le stationnement complet du camion Czech 3 est deja actif.");
            InstallOne(gamePath, MechanicPath, PatchMechanic, ValidateMechanic,
                journal, prepared, progress,
                "Restauration de l'arret du dialogue du mecanicien Czech 3...",
                "L'arret du dialogue du mecanicien Czech 3 est deja actif.");
            InstallOne(gamePath, RadioOperatorPath, PatchRadioOperator,
                ValidateRadioOperator, journal, prepared, progress,
                "Restauration du poste de precision du radio-operateur Czech 3...",
                "Le poste de precision du radio-operateur Czech 3 est deja actif.");
            InstallerCore.Log(
                "Czech 3 : manoeuvre du camion, reaction du mecanicien et "
                + "poste du radio-operateur reactives.");
        }

        private static void InstallOne(
            string gamePath, string relative,
            Func<byte[], byte[]> patch, Action<byte[]> validate,
            StateJournal journal, HashSet<string> prepared,
            Action<string> progress, string startMessage, string activeMessage)
        {
            InstallerCore.Report(progress, startMessage);
            DormantSource source = ResolveSource(
                gamePath, relative, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = patch(original);
            validate(patched);
            if (BytesEqual(original, patched))
            {
                InstallerCore.Report(progress, activeMessage);
                return;
            }

            InstallerCore.PrepareTarget(
                gamePath, relative, target, journal, prepared);
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            string temporary = target + ".hd2pack.tmp";
            try
            {
                File.WriteAllBytes(temporary, patched);
                File.Copy(temporary, target, true);
                journal.RecordHash(relative,
                    CmpInstaller.ComputeSha256(temporary));
            }
            finally
            {
                if (File.Exists(temporary)) File.Delete(temporary);
            }
        }

        private static byte[] PatchTruck(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsTruckPatched(text))
            {
                ValidateTruck(data);
                return data;
            }

            text = ReplaceDormantLine(text,
                "HUMAN_Drive(\"BMW_16\",5);",
                "HUMAN_Drive(\"BMW_16\",5);");
            text = ReplaceDormantLine(text,
                "HUMAN_Drive(\"couvej1\",5);",
                "HUMAN_Drive(\"couvej1\",5);");
            text = ReplaceDormantLine(text,
                "HUMAN_Drive(\"couvej1\",-3);",
                "HUMAN_Drive(\"couvej1\",-3);");
            text = ReplaceDormantLine(text,
                "HUMAN_Drive(\"couvej3\",-3);",
                "HUMAN_Drive(\"couvej3\",-3);");
            return ansi.GetBytes(text);
        }

        private static bool IsTruckPatched(string text)
        {
            return ContainsOrderedActiveLines(text, new[] {
                "HUMAN_Drive(\"BMW_15\",10);",
                "HUMAN_Drive(\"BMW_16\",5);",
                "HUMAN_Drive(\"couvej1\",5);",
                "HUMAN_Drive(\"opelbrzdi\",12);",
                "HUMAN_Drive(\"couvej1\",-3);",
                "HUMAN_Drive(\"couvej2\",-3);",
                "HUMAN_Drive(\"couvej3\",-3);",
                "HUMAN_Drive(\"couvej4\",-5);"
            });
        }

        private static void ValidateTruck(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsTruckPatched(text))
                throw new InvalidDataException(
                    "Manoeuvre restauree du camion Czech 3 incomplete.");
            RequireActiveLine(text, "HUMAN_Drive(\"BMW_16\",5);",
                "Nombre inattendu de passages du camion par BMW_16.");
            RequireActiveLine(text, "HUMAN_Drive(\"couvej1\",5);",
                "Nombre inattendu d'approches du camion par couvej1.");
            RequireActiveLine(text, "HUMAN_Drive(\"couvej1\",-3);",
                "Nombre inattendu de reculs du camion par couvej1.");
            RequireActiveLine(text, "HUMAN_Drive(\"couvej3\",-3);",
                "Nombre inattendu de reculs du camion par couvej3.");
        }

        private static byte[] PatchMechanic(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsMechanicPatched(text))
            {
                ValidateMechanic(data);
                return data;
            }
            text = ReplaceDormantLine(text,
                "sendsignal (kecac,2);", "SendSignal(kecac,2);");
            return ansi.GetBytes(text);
        }

        private static bool IsMechanicPatched(string text)
        {
            Match death = Regex.Match(text,
                @"OnDeath\s*\(\s*\)\s*\{(?<body>[\s\S]{0,420}?)\}",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
            return death.Success
                && HasActiveLine(
                    death.Groups["body"].Value, "SendSignal(kecac,2);");
        }

        private static void ValidateMechanic(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsMechanicPatched(text))
                throw new InvalidDataException(
                    "Reaction restauree du mecanicien Czech 3 incomplete.");
            RequireActiveLine(text, "SendSignal(kecac,2);",
                "Nombre inattendu d'arrets du dialogue du mecanicien.");
        }

        private static byte[] PatchRadioOperator(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsRadioOperatorPatched(text))
            {
                ValidateRadioOperator(data);
                return data;
            }
            text = ReplaceDormantLine(text,
                "HUMAN_SetSniper(1, 1);", "HUMAN_SetSniper(1, 1);");
            return ansi.GetBytes(text);
        }

        private static bool IsRadioOperatorPatched(string text)
        {
            return ContainsOrderedActiveLines(text, new[] {
                "HUMAN_WeaponOnArm(1);",
                "HUMAN_Move(\"spojar1\");",
                "HUMAN_SETMODE_Crouch();",
                "HUMAN_TurnAt(cum);",
                "HUMAN_SetSniper(1, 1);"
            });
        }

        private static void ValidateRadioOperator(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            if (!IsRadioOperatorPatched(text))
                throw new InvalidDataException(
                    "Poste restaure du radio-operateur Czech 3 incomplet.");
            RequireActiveLine(text, "HUMAN_SetSniper(1, 1);",
                "Nombre inattendu d'activations du radio-operateur.");
        }

        private static string ReplaceDormantLine(
            string text, string dormantInstruction, string activeInstruction)
        {
            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//[ \t]*"
                + Regex.Escape(dormantInstruction)
                + @"[ \t]*(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != 1)
                throw new InvalidDataException(
                    "Instruction dormante Czech 3 introuvable : "
                    + dormantInstruction);
            return dormant.Replace(text, match =>
                match.Groups["indent"].Value + activeInstruction, 1);
        }

        private static void RequireActiveLine(
            string text, string instruction, string message)
        {
            if (CountActiveLines(text, instruction) != 1)
                throw new InvalidDataException(message);
        }

        private static bool HasActiveLine(string text, string instruction)
        {
            return CountActiveLines(text, instruction) > 0;
        }

        private static int CountActiveLines(string text, string instruction)
        {
            string pattern = @"(?m)^[ \t]*" + Regex.Escape(instruction)
                + @"[ \t]*(?=\r?$)";
            return Regex.Matches(text, pattern,
                RegexOptions.IgnoreCase).Count;
        }

        private static bool ContainsOrderedActiveLines(
            string text, string[] instructions)
        {
            int offset = 0;
            foreach (string instruction in instructions)
            {
                Regex activeLine = new Regex(
                    @"(?m)^[ \t]*" + Regex.Escape(instruction)
                    + @"[ \t]*(?=\r?$)",
                    RegexOptions.IgnoreCase);
                Match found = activeLine.Match(text, offset);
                if (!found.Success) return false;
                offset = found.Index + found.Length;
            }
            return true;
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "opel_driver", "opel_driver.scr")
                || !HasBinding(registry, "mechanik", "R_cz3_pila_kladivo.scr")
                || !HasBinding(registry,
                    "mechanik_kecac", "mechanik_kecac.scr")
                || !HasBinding(registry, "radista", "Radista.scr"))
                throw new InvalidDataException(
                    "Liaisons commerciales du camion, du mecanicien ou du radio-operateur Czech 3 absentes.");

            string checkpoints = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, CheckpointPath, MissionArchives)));
            foreach (string point in new[] {
                "BMW_16", "couvej1", "couvej2", "couvej3", "couvej4", "spojar1"
            })
                if (checkpoints.IndexOf(point,
                        StringComparison.OrdinalIgnoreCase) < 0)
                    throw new InvalidDataException(
                        "Point officiel Czech 3 absent : " + point + ".");

            string scene = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath, ScenePath, MissionArchives)));
            if (scene.IndexOf("spojarcum",
                    StringComparison.OrdinalIgnoreCase) < 0)
                throw new InvalidDataException(
                    "Cadre de visee spojarcum absent de Czech 3.");

            string listener = Encoding.GetEncoding(1252).GetString(ReadSource(
                ResolveSource(gamePath,
                    "Scripts/CZECH3/mechanik_kecac.scr", ScriptArchives)));
            if (!Regex.IsMatch(listener,
                    @"Whenever\s+death\s*\(\s*_SignalReceived\s*\(\s*2\s*\)\s*\)"
                    + @"[\s\S]{0,180}DisableWhenevers\s*\(\s*1\s*\)",
                    RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(
                    "Recepteur officiel de mort du mecanicien Czech 3 absent.");
        }

        private static bool IsTargetActive(
            string gamePath, string relative, Action<byte[]> validate)
        {
            try
            {
                string target = InstallerCore.SafeGameTarget(gamePath, relative);
                if (!File.Exists(target)) return false;
                validate(File.ReadAllBytes(target));
                return true;
            }
            catch
            {
                return false;
            }
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException(
                    "Registre de scripts Czech 3 trop court.");
            int offset = 6;
            while (offset < data.Length)
            {
                string actor = ReadRegistryField(data, ref offset);
                string script = ReadRegistryField(data, ref offset);
                if (String.Equals(actor, wantedActor,
                        StringComparison.OrdinalIgnoreCase)
                    && String.Equals(script, wantedScript,
                        StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }

        private static string ReadRegistryField(byte[] data, ref int offset)
        {
            if (offset + 6 > data.Length)
                throw new InvalidDataException(
                    "Registre de scripts Czech 3 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException(
                    "Champ invalide dans le registre Czech 3.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
        }

        private static DormantSource ResolveSource(
            string gamePath, string relative, string[] archiveNames)
        {
            InstallerCore.ValidateGamePath(gamePath);
            DormantSource result = null;
            foreach (string archiveName in archiveNames)
            {
                string archivePath = Path.Combine(gamePath, archiveName);
                if (!File.Exists(archivePath))
                    throw new FileNotFoundException(
                        "Archive officielle manquante.", archivePath);
                using (DtaArchive archive = new DtaArchive(archivePath))
                    foreach (DtaEntry entry in archive.Entries)
                        if (String.Equals(
                            entry.Name.Replace((char)92, '/'), relative,
                            StringComparison.OrdinalIgnoreCase))
                            result = new DormantSource {
                                ArchivePath = archivePath,
                                EntryIndex = entry.Index
                            };
            }
            if (result == null)
                throw new InvalidDataException(
                    "Donnee officielle introuvable : " + relative);
            return result;
        }

        private static byte[] ReadSource(DormantSource source)
        {
            using (DtaArchive archive = new DtaArchive(source.ArchivePath))
                return archive.Read(archive.Entries[source.EntryIndex]);
        }

        private static bool BytesEqual(byte[] left, byte[] right)
        {
            if (left.Length != right.Length) return false;
            for (int index = 0; index < left.Length; index++)
                if (left[index] != right[index]) return false;
            return true;
        }
    }
}
