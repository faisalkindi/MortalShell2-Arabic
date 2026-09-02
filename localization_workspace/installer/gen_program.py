"""Generate Program.cs for the Mortal Shell II Arabic installer.

Reuses the Elliot installer's UI verbatim (proven, shipped) and swaps the core for the MS2
case, which is far simpler: the mod is six `_P` patch files dropped next to the game's own
paks. No base-pak rebuild, no repak, no AES key, no backup - uninstall deletes the six files.
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC = r"C:\Users\Faisal\Ai\Mods Dev\Elliot\localization_workspace\installer\Program.cs"
s = open(SRC, encoding="utf-8").read()

CORE = r'''    static class Program
    {
        const string AppId = "2584270";            // Mortal Shell II (Steam install dir "Sparta")
        static readonly string[] ModFiles =
        {
            "pakchunk9998-Windows_P.pak", "pakchunk9998-Windows_P.ucas", "pakchunk9998-Windows_P.utoc",
            "zzz_ArabicLang_P.pak",       "zzz_ArabicLang_P.ucas",       "zzz_ArabicLang_P.utoc"
        };
        const string InstalledMarker = "zzz_ArabicLang_P.utoc";

        [STAThread]
        static int Main(string[] args)
        {
            // headless mode for testing: --detect | --install <root> | --uninstall <root>
            if (args.Length > 0)
            {
                try
                {
                    if (args[0] == "--detect") { Console.WriteLine(DetectGamePath() ?? "(not found)"); return 0; }
                    if (args[0] == "--install")   { Install(args[1], Console.WriteLine);   return 0; }
                    if (args[0] == "--uninstall") { Uninstall(args[1], Console.WriteLine); return 0; }
                }
                catch (Exception ex) { Console.Error.WriteLine(ex.Message); return 1; }
            }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(true);
            Application.Run(new MainForm());
            return 0;
        }

        // ---- Steam game-folder detection -------------------------------------
        public static string DetectGamePath()
        {
            try
            {
                string steam = GetSteamPath();
                if (steam == null) return null;
                string vdf = Path.Combine(steam, "steamapps", "libraryfolders.vdf");
                var libs = new System.Collections.Generic.List<string> { steam };
                if (File.Exists(vdf))
                    foreach (Match m in Regex.Matches(File.ReadAllText(vdf), "\"path\"\\s*\"([^\"]+)\""))
                        libs.Add(m.Groups[1].Value.Replace("\\\\", "\\"));
                foreach (string lib in libs)
                {
                    string acf = Path.Combine(lib, "steamapps", "appmanifest_" + AppId + ".acf");
                    if (!File.Exists(acf)) continue;
                    var im = Regex.Match(File.ReadAllText(acf), "\"installdir\"\\s*\"([^\"]+)\"");
                    if (!im.Success) continue;
                    string game = Path.Combine(lib, "steamapps", "common", im.Groups[1].Value);
                    if (IsValidGameFolder(game)) return game;
                }
            }
            catch { }
            return null;
        }

        static string GetSteamPath()
        {
            try { if (Registry.GetValue(@"HKEY_CURRENT_USER\Software\Valve\Steam", "SteamPath", null) is string s1 && Directory.Exists(s1)) return s1.Replace('/', '\\'); } catch { }
            try { if (Registry.GetValue(@"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath", null) is string s2 && Directory.Exists(s2)) return s2; } catch { }
            return null;
        }

        // ---- path helpers -----------------------------------------------------
        public static string PaksDir(string gameRoot) => Path.Combine(gameRoot, "MortalShell2", "Content", "Paks");
        public static bool IsValidGameFolder(string folder) =>
            !string.IsNullOrEmpty(folder) && File.Exists(Path.Combine(PaksDir(folder), "pakchunk0-Windows.pak"));
        public static bool IsInstalled(string gameRoot) => File.Exists(Path.Combine(PaksDir(gameRoot), InstalledMarker));

        // ---- install / uninstall ---------------------------------------------
        // Nothing of the game is modified: the mod is six patch files (_P) dropped next to the
        // game's own paks. Uninstall = delete those six. No backup needed.
        public static void Install(string gameRoot, Action<string> progress)
        {
            string paks = PaksDir(gameRoot);
            if (!Directory.Exists(paks)) throw new Exception("لم يُعثر على مجلد اللعبة:\nMortalShell2\\Content\\Paks");
            EnsureGameClosed(Path.Combine(paks, "pakchunk0-Windows.pak"));
            progress("جارٍ تثبيت ملفات التعريب…");
            var asm = Assembly.GetExecutingAssembly();
            using (Stream s = asm.GetManifestResourceStream("payload.zip"))
            {
                if (s == null) throw new Exception("ملفات التعريب المضمّنة غير موجودة داخل المثبّت.");
                using (var z = new ZipArchive(s, ZipArchiveMode.Read))
                    foreach (string f in ModFiles)
                    {
                        var entry = z.GetEntry(f);
                        if (entry == null) throw new Exception("ملف مفقود داخل المثبّت: " + f);
                        entry.ExtractToFile(Path.Combine(paks, f), true);
                    }
            }
            progress("تم التثبيت بنجاح ✔");
        }

        public static void Uninstall(string gameRoot, Action<string> progress)
        {
            string paks = PaksDir(gameRoot);
            EnsureGameClosed(Path.Combine(paks, "pakchunk0-Windows.pak"));
            progress("جارٍ إزالة ملفات التعريب…");
            foreach (string f in ModFiles) { string p = Path.Combine(paks, f); if (File.Exists(p)) File.Delete(p); }
            progress("تمت الإزالة ✔");
        }

        static void EnsureGameClosed(string probeFile)
        {
            if (!File.Exists(probeFile)) return;
            try { using (new FileStream(probeFile, FileMode.Open, FileAccess.ReadWrite, FileShare.None)) { } }
            catch (IOException) { throw new Exception("اللعبة قيد التشغيل. الرجاء إغلاق اللعبة تمامًا ثم إعادة المحاولة."); }
            catch (UnauthorizedAccessException) { throw new Exception("تعذّر الوصول إلى مجلد اللعبة. شغّل المثبّت كمسؤول (Run as administrator)."); }
        }
    }

'''

start = s.index("    static class Program")
end = s.index("    // ===================== modern UI")
s = s[:start] + CORE + s[end:]
s = s.replace("namespace ElliotArabic", "namespace MortalShell2Arabic")

REPL = [
    ('"اختر مجلد اللعبة (المجلد الذي يحتوي على Elliot)"',
     '"اختر مجلد اللعبة (المجلد الذي يحتوي على MortalShell2)"'),
    ('string sub = Path.Combine(chosen, "The Adventures of Elliot_The Millennium Tales");',
     'string sub = Path.Combine(chosen, "Sparta");'),
    ('"هذا المجلد لا يحتوي على ملفات اللعبة (Elliot\\\\Content\\\\Paks)."',
     '"هذا المجلد لا يحتوي على ملفات اللعبة (MortalShell2\\\\Content\\\\Paks)."'),
    ('                    "سيتم تعديل ملف اللعبة لإضافة اللغة العربية.\\n" +\n'
     '                    "تأكد من إغلاق اللعبة، وتوفّر مساحة فارغة (~8 جيجابايت).\\n\\nالمتابعة؟",',
     '                    "سيتم إضافة ملفات التعريب إلى مجلد اللعبة (لا يتم تعديل أي ملف أصلي).\\n" +\n'
     '                    "تأكد من إغلاق اللعبة.\\n\\nالمتابعة؟",'),
    ('"تم تثبيت اللغة العربية بنجاح!\\n\\nشغّل اللعبة، ثم اذهب إلى:\\nالإعدادات ← اللغة ← اختر «العربية»\\n(تظهر مكان «Italiano»).",',
     '"تم تثبيت اللغة العربية بنجاح!\\n\\nشغّل اللعبة، ثم اذهب إلى:\\nالإعدادات ← اللعبة ← اللغة ← اختر «العربية»\\nسيتم حفظ اختيارك للمرات القادمة.",'),
]
for old, new in REPL:
    assert old in s, "anchor missing: " + old[:50]
    s = s.replace(old, new)

low = s.lower()
assert "elliotarabic" not in low and "elliot-windows" not in low and "repak" not in low and "aeskey" not in low
open("Program.cs", "w", encoding="utf-8").write(s)
print("Program.cs written:", len(s.splitlines()), "lines")
