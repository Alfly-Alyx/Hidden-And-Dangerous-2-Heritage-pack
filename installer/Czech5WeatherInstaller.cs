using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace HD2CommunityInstaller
{
    internal static class Czech5WeatherInstaller
    {
        private const string WeatherPath = "Scripts/CZECH5/R_Cz4B_pocasi.scr";
        private const string LightningPath = "Scripts/CZECH5/R_Cz4B_lightnings.scr";
        private const string RegistryPath = "Missions/CZECH5/Scripts.dta";

        private static readonly string[] ScriptArchives = {
            "Scripts.dta", "Patch.dta", "SabreSquadron.dta"
        };

        private static readonly string[] MissionArchives = {
            "missions.dta", "Patch.dta", "SabreSquadron.dta"
        };

        public static string ValidateOnly(string gamePath)
        {
            byte[] weatherOriginal = ReadSource(ResolveSource(
                gamePath, WeatherPath, ScriptArchives));
            byte[] lightningOriginal = ReadSource(ResolveSource(
                gamePath, LightningPath, ScriptArchives));
            byte[] weatherPatched = PatchWeather(weatherOriginal);
            byte[] lightningPatched = PatchLightning(lightningOriginal);
            if (BytesEqual(weatherOriginal, weatherPatched)
                || BytesEqual(lightningOriginal, lightningPatched))
                throw new InvalidDataException(
                    "La meteo ou les eclairs Czech 5 semblent deja restaures.");
            ValidateWeather(weatherPatched);
            ValidateLightning(lightningPatched);
            if (!BytesEqual(weatherPatched, PatchWeather(weatherPatched))
                || !BytesEqual(lightningPatched, PatchLightning(lightningPatched)))
                throw new InvalidDataException(
                    "La restauration de la meteo Czech 5 n'est pas idempotente.");
            ValidateAssets(gamePath);
            return "Czech 5 verifie : la meteo et les eclairs officiels "
                + "entierement commentes sont restaurables.";
        }

        public static bool IsActive(string gamePath)
        {
            try
            {
                string weather = InstallerCore.SafeGameTarget(gamePath, WeatherPath);
                string lightning = InstallerCore.SafeGameTarget(gamePath, LightningPath);
                if (!File.Exists(weather) || !File.Exists(lightning)) return false;
                ValidateWeather(File.ReadAllBytes(weather));
                ValidateLightning(File.ReadAllBytes(lightning));
                return true;
            }
            catch
            {
                return false;
            }
        }

        public static void Install(
            string gamePath, StateJournal journal, HashSet<string> prepared,
            Action<string> progress)
        {
            InstallerCore.Report(progress,
                "Restauration de la meteo et des eclairs dans Czech 5...");
            ValidateAssets(gamePath);
            List<ScriptChange> changes = new List<ScriptChange> {
                BuildChange(gamePath, WeatherPath, true),
                BuildChange(gamePath, LightningPath, false)
            };
            int written = 0;
            foreach (ScriptChange change in changes)
            {
                if (BytesEqual(change.Original, change.Patched)) continue;
                InstallerCore.PrepareTarget(
                    gamePath, change.Relative, change.Target, journal, prepared);
                Directory.CreateDirectory(Path.GetDirectoryName(change.Target));
                string temporary = change.Target + ".hd2pack.tmp";
                try
                {
                    File.WriteAllBytes(temporary, change.Patched);
                    File.Copy(temporary, change.Target, true);
                    journal.RecordHash(
                        change.Relative, CmpInstaller.ComputeSha256(temporary));
                }
                finally
                {
                    if (File.Exists(temporary)) File.Delete(temporary);
                }
                written++;
            }
            if (written == 0)
            {
                InstallerCore.Report(progress,
                    "La meteo et les eclairs Czech 5 sont deja actifs.");
                return;
            }
            InstallerCore.Log(
                "Czech 5 : scripts officiels de meteo et d'eclairs restaures.");
            InstallerCore.Report(progress,
                "La meteo et les eclairs officiels de Czech 5 sont reactives.");
        }

        private static ScriptChange BuildChange(
            string gamePath, string relative, bool weather)
        {
            DormantSource source = ResolveSource(
                gamePath, relative, ScriptArchives);
            string target = InstallerCore.SafeGameTarget(gamePath, relative);
            byte[] original = File.Exists(target)
                ? File.ReadAllBytes(target) : ReadSource(source);
            byte[] patched = weather
                ? PatchWeather(original) : PatchLightning(original);
            if (weather) ValidateWeather(patched);
            else ValidateLightning(patched);
            return new ScriptChange {
                Relative = relative,
                Target = target,
                Original = original,
                Patched = patched
            };
        }

        private static byte[] PatchWeather(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsWeatherPatched(text))
            {
                ValidateWeather(data);
                return data;
            }
            RequireCount(text,
                @"(?m)^[ \t]*//[ \t]*WEATHER_Set(?:Count|ColorOut|ColorIn|Speed|Size|Space|Dir|On|Mode)\s*\(",
                9, "Le corps dormant de la meteo Czech 5 est incomplet.");
            text = UncommentLines(text,
                @"(?:integer\s+(?:count|speed|X|Y|Z)\b|WEATHER_Set(?:Count|ColorOut|ColorIn|Speed|Size|Space|Dir|On|Mode)\s*\()",
                14);
            return ansi.GetBytes(text);
        }

        private static byte[] PatchLightning(byte[] data)
        {
            Encoding ansi = Encoding.GetEncoding(1252);
            string text = ansi.GetString(data);
            if (IsLightningPatched(text))
            {
                ValidateLightning(data);
                return data;
            }
            text = UncommentLines(text,
                @"(?:integer\s+(?:time|wait)\b|frame\s+lightning\b|Label\s+loop\s*:|time\s*=|THUNDERSTORM_SetOn\s*\(|Delay\s*\(|wait\s*=|goto\s+loop\s*;)",
                11);
            return ansi.GetBytes(text);
        }

        private static string UncommentLines(
            string text, string bodyPattern, int expected)
        {
            Regex dormant = new Regex(
                @"(?m)^(?<indent>[ \t]*)//(?<space>[ \t]*)(?<body>"
                + bodyPattern + @"[^\r\n]*)(?=\r?$)",
                RegexOptions.IgnoreCase);
            if (dormant.Matches(text).Count != expected)
                throw new InvalidDataException(
                    "Nombre inattendu de lignes dormantes dans la meteo Czech 5.");
            return dormant.Replace(text, match =>
                match.Groups["indent"].Value + match.Groups["space"].Value
                + match.Groups["body"].Value);
        }

        private static bool IsWeatherPatched(string text)
        {
            return Regex.IsMatch(text,
                @"(?m)^[ \t]*WEATHER_SetCount\s*\(\s*count\s*\)\s*;"
                + @"[\s\S]{0,900}^[ \t]*WEATHER_SetOn\s*\(\s*1\s*\)\s*;"
                + @"[\s\S]{0,120}^[ \t]*WEATHER_SetMode\s*\(\s*0\s*\)\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static bool IsLightningPatched(string text)
        {
            return Regex.IsMatch(text,
                @"Label\s+loop\s*:[\s\S]{0,180}"
                + @"THUNDERSTORM_SetOn\s*\(\s*true\s*,\s*lightning\s*\)\s*;"
                + @"[\s\S]{0,180}THUNDERSTORM_SetOn\s*\(\s*false\s*,\s*lightning\s*\)\s*;"
                + @"[\s\S]{0,220}goto\s+loop\s*;",
                RegexOptions.IgnoreCase | RegexOptions.Multiline);
        }

        private static void ValidateWeather(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            Require(text, @"(?m)^[ \t]*integer\s+count\s*;[ \t]*count\s*=\s*2000\s*;",
                "Le volume de meteo Czech 5 est absent.");
            Require(text, @"(?m)^[ \t]*integer\s+speed\s*;[ \t]*speed\s*=\s*25000\s*;",
                "La vitesse de meteo Czech 5 est absente.");
            Require(text,
                @"WEATHER_SetColorOut\s*\(\s*32\s*,\s*23\s*,\s*21\s*,\s*0\s*\)\s*;"
                + @"[\s\S]{0,180}WEATHER_SetColorIn\s*\(\s*38\s*,\s*27\s*,\s*26\s*,\s*128\s*\)\s*;"
                + @"[\s\S]{0,400}WEATHER_SetOn\s*\(\s*1\s*\)\s*;"
                + @"[\s\S]{0,100}WEATHER_SetMode\s*\(\s*0\s*\)\s*;",
                "La configuration de meteo Czech 5 est incomplete.");
            RequireCount(text,
                @"(?m)^[ \t]*//[ \t]*THUNDERSTORM_SetOn\s*\(\s*-integer-",
                1, "Le gabarit invalide d'orage Czech 5 ne doit pas etre active.");
        }

        private static void ValidateLightning(byte[] data)
        {
            string text = Encoding.GetEncoding(1252).GetString(data);
            Require(text,
                @"frame\s+lightning\s*;[\s\S]{0,100}"
                + @"FRM_GetMyFrame\s*\(\s*lightning\s*\)\s*;[\s\S]{0,120}"
                + @"Label\s+loop\s*:[\s\S]{0,180}"
                + @"THUNDERSTORM_SetOn\s*\(\s*true\s*,\s*lightning\s*\)\s*;"
                + @"[\s\S]{0,180}THUNDERSTORM_SetOn\s*\(\s*false\s*,\s*lightning\s*\)\s*;"
                + @"[\s\S]{0,220}goto\s+loop\s*;",
                "La boucle d'eclairs Czech 5 est incomplete.");
        }

        private static void ValidateAssets(string gamePath)
        {
            byte[] registry = ReadSource(ResolveSource(
                gamePath, RegistryPath, MissionArchives));
            if (!HasBinding(registry, "3crib144", "R_Cz4B_pocasi.scr")
                || !HasBinding(registry,
                    "light_lightnings", "R_Cz4B_lightnings.scr"))
                throw new InvalidDataException(
                    "Les liaisons officielles de la meteo Czech 5 sont incompletes.");
            ValidateReference(gamePath,
                "Scripts/TUTORIAL/T_EE_Weather.scr", "WEATHER_SetOn");
            ValidateReference(gamePath,
                "Scripts/TUTORIAL/T_EE_Light.scr", "THUNDERSTORM_SetOn");
        }

        private static void ValidateReference(
            string gamePath, string relative, string function)
        {
            string text = Encoding.GetEncoding(1252).GetString(
                ReadSource(ResolveSource(gamePath, relative, ScriptArchives)));
            Require(text, @"(?m)^[ \t]*" + Regex.Escape(function) + @"\s*\(",
                "Commande meteo officielle non confirmee dans " + relative + ".");
        }

        private static bool HasBinding(
            byte[] data, string wantedActor, string wantedScript)
        {
            if (data == null || data.Length < 6)
                throw new InvalidDataException("Registre Czech 5 trop court.");
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
                throw new InvalidDataException("Registre Czech 5 tronque.");
            ushort marker = BitConverter.ToUInt16(data, offset);
            int total = checked((int)BitConverter.ToUInt32(data, offset + 2));
            if (marker != 1 || total < 7 || offset + total > data.Length
                || data[offset + total - 1] != 0)
                throw new InvalidDataException("Champ invalide dans le registre Czech 5.");
            string value = Encoding.GetEncoding(1252).GetString(
                data, offset + 6, total - 7);
            offset += total;
            return value;
        }

        private static void Require(string text, string pattern, string message)
        {
            if (!Regex.IsMatch(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline))
                throw new InvalidDataException(message);
        }

        private static void RequireCount(
            string text, string pattern, int expected, string message)
        {
            if (Regex.Matches(text, pattern,
                RegexOptions.IgnoreCase | RegexOptions.Multiline).Count != expected)
                throw new InvalidDataException(message);
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

        private sealed class ScriptChange
        {
            public string Relative;
            public string Target;
            public byte[] Original;
            public byte[] Patched;
        }
    }
}