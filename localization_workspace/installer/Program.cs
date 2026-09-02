using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

namespace MortalShell2Arabic
{
    static class Program
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

    // ===================== modern UI =====================

    static class Ui
    {
        public static readonly Color Bg = Color.FromArgb(16, 18, 20);
        public static readonly Color Card = Color.FromArgb(30, 34, 38);
        public static readonly Color Gold = Color.FromArgb(186, 204, 213)   /* steel: logo lettering */;
        public static readonly Color GoldHover = Color.FromArgb(211, 225, 232);
        public static readonly Color Red = Color.FromArgb(190, 0, 0)        /* the II */;
        public static readonly Color RedHover = Color.FromArgb(214, 24, 24);
        public static readonly Color Ink = Color.FromArgb(12, 13, 15);
        public static readonly Color Text = Color.FromArgb(226, 232, 236);
        public static readonly Color Muted = Color.FromArgb(128, 140, 148);

        static PrivateFontCollection _pfc;
        public static FontFamily Family;

        public static void LoadFont()
        {
            try
            {
                var asm = Assembly.GetExecutingAssembly();
                using (Stream s = asm.GetManifestResourceStream("ui_font.ttf"))
                {
                    byte[] data = new byte[s.Length];
                    s.Read(data, 0, data.Length);
                    IntPtr ptr = Marshal.AllocCoTaskMem(data.Length);
                    Marshal.Copy(data, 0, ptr, data.Length);
                    _pfc = new PrivateFontCollection();
                    _pfc.AddMemoryFont(ptr, data.Length);
                    Marshal.FreeCoTaskMem(ptr);
                    Family = _pfc.Families[0];
                }
            }
            catch { Family = new FontFamily("Tahoma"); }
        }

        public static Font F(float size, FontStyle style = FontStyle.Regular)
            => new Font(Family, size, style, GraphicsUnit.Point);

        public static Image LoadBackground()
        {
            try
            {
                using (Stream st = Assembly.GetExecutingAssembly().GetManifestResourceStream("ui_bg.jpg"))
                using (var img = Image.FromStream(st))
                    return new Bitmap(img);
            }
            catch { return null; }
        }

        public static Image LoadLogo()
        {
            try
            {
                using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream("ui_logo.png"))
                using (var img = Image.FromStream(s))
                    return new Bitmap(img);
            }
            catch { return null; }
        }

        public static GraphicsPath Round(Rectangle r, int radius)
        {
            int d = radius * 2;
            var p = new GraphicsPath();
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }
    }

    public class RoundButton : Button
    {
        public Color Base = Ui.Gold;
        public Color Hover = Ui.GoldHover;
        public Color Fg = Ui.Ink;
        public int Radius = 14;
        public Color Outline = Color.Empty;
        bool _hover;

        public RoundButton()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint
                     | ControlStyles.OptimizedDoubleBuffer | ControlStyles.SupportsTransparentBackColor, true);
            FlatStyle = FlatStyle.Flat;
            FlatAppearance.BorderSize = 0;
            BackColor = Color.Transparent;
            Cursor = Cursors.Hand;
            MouseEnter += (s, e) => { _hover = true; Invalidate(); };
            MouseLeave += (s, e) => { _hover = false; Invalidate(); };
        }

        protected override void OnPaintBackground(PaintEventArgs e) { }

        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.ClearTypeGridFit;
            var rect = new Rectangle(0, 0, Width - 1, Height - 1);
            Color fill = !Enabled ? Color.FromArgb(70, 64, 58) : (_hover ? Hover : Base);
            using (var path = Ui.Round(rect, Radius))
            using (var b = new SolidBrush(fill))
            {
                g.FillPath(b, path);
                if (Outline != Color.Empty) using (var pen = new Pen(Outline, 1f)) g.DrawPath(pen, path);
            }
            var sf = new StringFormat(StringFormatFlags.DirectionRightToLeft)
            { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center };
            using (var tb = new SolidBrush(Enabled ? Fg : Color.FromArgb(140, 130, 120)))
                g.DrawString(Text, Font, tb, rect, sf);
        }
    }

    public class MainForm : Form
    {
        string gamePath;
        Label lblStatus, lblPath;
        RoundButton btnInstall, btnUninstall;
        LinkLabel btnBrowse;
        bool busy;

        public MainForm()
        {
            Ui.LoadFont();

            AutoScaleMode = AutoScaleMode.Dpi;
            AutoScaleDimensions = new SizeF(96F, 96F);
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(560, 780);
            BackColor = Ui.Bg;
            BackgroundImage = Ui.LoadBackground();
            BackgroundImageLayout = ImageLayout.Stretch;
            RightToLeft = RightToLeft.Yes;
            RightToLeftLayout = true;
            Font = Ui.F(11f);
            Text = "Mortal Shell II Arabic Installer";
            MouseDown += DragStart;

            var close = new Label
            {
                Text = "✕", Font = new Font("Segoe UI", 12f, FontStyle.Bold), ForeColor = Ui.Muted,
                AutoSize = false, Size = new Size(34, 30), Location = new Point(14, 14),
                TextAlign = ContentAlignment.MiddleCenter, Cursor = Cursors.Hand, BackColor = Color.Transparent
            };
            close.Click += (s, e) => Close();
            close.MouseEnter += (s, e) => { close.ForeColor = Ui.Red; };
            close.MouseLeave += (s, e) => { close.ForeColor = Ui.Muted; };
            Controls.Add(close);

            var logo = new PictureBox
            {
                Image = Ui.LoadLogo(), SizeMode = PictureBoxSizeMode.Zoom, BackColor = Color.Transparent,
                Size = new Size(440, 208), Location = new Point((ClientSize.Width - 440) / 2, 34)
            };
            logo.MouseDown += DragStart;
            Controls.Add(logo);

            var subtitle = new Label
            {
                Text = "التعريب العربي الكامل", Font = Ui.F(18f, FontStyle.Bold), ForeColor = Ui.Gold,
                AutoSize = false, UseCompatibleTextRendering = true, TextAlign = ContentAlignment.MiddleCenter,
                Size = new Size(ClientSize.Width, 58), Location = new Point(0, 242), BackColor = Color.Transparent
            };
            subtitle.MouseDown += DragStart; Controls.Add(subtitle);

            var tagline = new Label
            {
                Text = "ترجمة كاملة لكل نصوص اللعبة · واجهة معرّبة بالكامل",
                Font = Ui.F(9f), ForeColor = Ui.Muted,
                AutoSize = false, UseCompatibleTextRendering = true, TextAlign = ContentAlignment.MiddleCenter,
                Size = new Size(ClientSize.Width, 30), Location = new Point(0, 298), BackColor = Color.Transparent
            };
            tagline.MouseDown += DragStart; Controls.Add(tagline);

            var card = new RoundPanel
            {
                Size = new Size(480, 86), Location = new Point((ClientSize.Width - 480) / 2, 334),
                Fill = Color.FromArgb(205, Ui.Card), Border = Color.FromArgb(60, Ui.Gold)
            };
            lblPath = new Label
            {
                AutoSize = false, Dock = DockStyle.Fill, Padding = new Padding(6, 4, 6, 4), ForeColor = Ui.Text,
                Font = Ui.F(8.5f), UseCompatibleTextRendering = true, TextAlign = ContentAlignment.MiddleCenter, BackColor = Color.Transparent
            };
            card.Controls.Add(lblPath); Controls.Add(card);

            btnInstall = new RoundButton
            {
                Text = "تثبيت اللغة العربية", Font = Ui.F(15f, FontStyle.Bold), Size = new Size(480, 64),
                Location = new Point((ClientSize.Width - 480) / 2, 440), Base = Ui.Red, Hover = Ui.RedHover, Fg = Color.White, Radius = 14
            };
            btnInstall.Click += OnInstall; Controls.Add(btnInstall);

            btnUninstall = new RoundButton
            {
                Text = "إزالة اللغة العربية", Font = Ui.F(12f, FontStyle.Bold), Size = new Size(480, 52),
                Location = new Point((ClientSize.Width - 480) / 2, 514), Base = Color.FromArgb(28, Ui.Gold), Hover = Color.FromArgb(60, Ui.Gold),
                Fg = Ui.Gold, Outline = Color.FromArgb(150, Ui.Gold), Radius = 14
            };
            btnUninstall.Click += OnUninstall; Controls.Add(btnUninstall);

            lblStatus = new Label
            {
                AutoSize = false, Font = Ui.F(10f), UseCompatibleTextRendering = true, TextAlign = ContentAlignment.MiddleCenter,
                ForeColor = Ui.Muted, Size = new Size(ClientSize.Width, 32), Location = new Point(0, 578), BackColor = Color.Transparent
            };
            lblStatus.MouseDown += DragStart; Controls.Add(lblStatus);

            btnBrowse = new LinkLabel
            {
                Text = "تحديد مجلد اللعبة يدويًا", AutoSize = false, Font = Ui.F(9f), LinkColor = Ui.Muted,
                ActiveLinkColor = Ui.Gold, LinkBehavior = LinkBehavior.HoverUnderline, TextAlign = ContentAlignment.MiddleCenter,
                Size = new Size(ClientSize.Width, 28), Location = new Point(0, 610), BackColor = Color.Transparent
            };
            btnBrowse.Click += OnBrowse; Controls.Add(btnBrowse);

            var kofi = new RoundButton
            {
                Text = "أعجبك التعريب؟ ادعمني على Ko-fi", Font = Ui.F(10.5f, FontStyle.Bold), Size = new Size(440, 46),
                Location = new Point((ClientSize.Width - 440) / 2, 676), Base = Color.FromArgb(22, Ui.Gold), Hover = Color.FromArgb(55, Ui.Gold),
                Fg = Ui.Text, Outline = Color.FromArgb(120, Ui.Gold), Radius = 23
            };
            kofi.Click += (s, e) => { try { Process.Start(new ProcessStartInfo("https://ko-fi.com/kindiboy") { UseShellExecute = true }); } catch { } };
            Controls.Add(kofi);

            var footer = new Label
            {
                Text = "تعريب وإعداد:  Kindiboy", Font = Ui.F(9.5f, FontStyle.Bold), ForeColor = Ui.Gold,
                AutoSize = false, UseCompatibleTextRendering = true, TextAlign = ContentAlignment.MiddleCenter,
                Size = new Size(ClientSize.Width, 28), Location = new Point(0, 736), BackColor = Color.Transparent
            };
            footer.MouseDown += DragStart; Controls.Add(footer);

            gamePath = Program.DetectGamePath();
            RefreshState();
        }

        protected override void OnSizeChanged(EventArgs e)
        {
            base.OnSizeChanged(e);
            // recompute after DPI auto-scaling so the rounded corners follow the real size
            Region = new Region(Ui.Round(new Rectangle(0, 0, Width, Height), (int)(20 * DeviceDpi / 96f)));
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            // subtle steel border
            using (var pen = new Pen(Color.FromArgb(70, Ui.Gold), 1))
            using (var path = Ui.Round(new Rectangle(0, 0, Width - 1, Height - 1), (int)(20 * DeviceDpi / 96f)))
            {
                e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
                e.Graphics.DrawPath(pen, path);
            }
        }

        // ---- drag-to-move (borderless) ----
        [DllImport("user32.dll")] static extern bool ReleaseCapture();
        [DllImport("user32.dll")] static extern IntPtr SendMessage(IntPtr h, int msg, int wp, int lp);
        void DragStart(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left)
            {
                ReleaseCapture();
                SendMessage(Handle, 0xA1, 0x2, 0);
            }
        }

        void RefreshState()
        {
            if (Program.IsValidGameFolder(gamePath))
            {
                bool installed = Program.IsInstalled(gamePath);
                lblPath.ForeColor = Ui.Text;
                lblPath.Text = "تم العثور على اللعبة" + Environment.NewLine + Trim(gamePath);
                btnInstall.Enabled = !busy;
                btnUninstall.Enabled = !busy && installed;
                if (installed) SetStatus("✔ اللغة العربية مُثبّتة حاليًا", Ui.Gold);
                else SetStatus("اللغة العربية غير مُثبّتة", Ui.Muted);
            }
            else
            {
                lblPath.ForeColor = Ui.Red;
                lblPath.Text = "لم يتم العثور على اللعبة" + Environment.NewLine + "الرجاء تحديد المجلد يدويًا";
                btnInstall.Enabled = false;
                btnUninstall.Enabled = false;
                SetStatus("في انتظار تحديد مجلد اللعبة", Ui.Muted);
            }
            btnInstall.Invalidate();
            btnUninstall.Invalidate();
        }

        static string Trim(string p)
        {
            if (p != null && p.Length > 30) p = "…" + p.Substring(p.Length - 28); return p == null ? null : "‪" + p + "‬";
            return p;
        }

        void SetStatus(string text, Color color)
        {
            lblStatus.Text = text;
            lblStatus.ForeColor = color;
        }

        void Progress(string text)
        {
            if (InvokeRequired) BeginInvoke(new Action(() => SetStatus(text, Ui.Gold)));
            else SetStatus(text, Ui.Gold);
        }

        void SetBusy(bool b)
        {
            busy = b;
            Cursor = b ? Cursors.WaitCursor : Cursors.Default;
            RefreshState();
        }

        void OnBrowse(object sender, EventArgs e)
        {
            if (busy) return;
            using (var dlg = new FolderBrowserDialog())
            {
                dlg.Description = "اختر مجلد اللعبة (المجلد الذي يحتوي على MortalShell2)";
                dlg.UseDescriptionForTitle = true;
                if (dlg.ShowDialog(this) == DialogResult.OK)
                {
                    string chosen = dlg.SelectedPath;
                    if (!Program.IsValidGameFolder(chosen))
                    {
                        string sub = Path.Combine(chosen, "Sparta");
                        if (Program.IsValidGameFolder(sub)) chosen = sub;
                    }
                    if (Program.IsValidGameFolder(chosen)) gamePath = chosen;
                    else MessageBox.Show(this, "هذا المجلد لا يحتوي على ملفات اللعبة (MortalShell2\\Content\\Paks).",
                        "مجلد غير صالح", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    RefreshState();
                }
            }
        }

        void OnInstall(object sender, EventArgs e)
        {
            if (busy) return;
            if (MessageBox.Show(this,
                    "سيتم إضافة ملفات التعريب إلى مجلد اللعبة (لا يتم تعديل أي ملف أصلي).\n" +
                    "تأكد من إغلاق اللعبة.\n\nالمتابعة؟",
                    "تثبيت", MessageBoxButtons.OKCancel, MessageBoxIcon.Question) != DialogResult.OK)
                return;

            SetBusy(true);
            string root = gamePath;
            var t = new Thread(() =>
            {
                try
                {
                    Program.Install(root, Progress);
                    BeginInvoke(new Action(() =>
                    {
                        SetBusy(false);
                        MessageBox.Show(this,
                            "تم تثبيت اللغة العربية بنجاح!\n\nشغّل اللعبة، ثم اذهب إلى:\nالإعدادات ← اللعبة ← اللغة ← اختر «العربية»\nسيتم حفظ اختيارك للمرات القادمة.",
                            "تم التثبيت", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }));
                }
                catch (Exception ex)
                {
                    BeginInvoke(new Action(() =>
                    {
                        SetBusy(false);
                        MessageBox.Show(this, ex.Message, "خطأ في التثبيت", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }));
                }
            });
            t.IsBackground = true;
            t.Start();
        }

        void OnUninstall(object sender, EventArgs e)
        {
            if (busy) return;
            SetBusy(true);
            string root = gamePath;
            var t = new Thread(() =>
            {
                try
                {
                    Program.Uninstall(root, Progress);
                    BeginInvoke(new Action(() =>
                    {
                        SetBusy(false);
                        MessageBox.Show(this, "تمت إزالة اللغة العربية. ستعود اللعبة إلى لغاتها الأصلية.",
                            "تمت الإزالة", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }));
                }
                catch (Exception ex)
                {
                    BeginInvoke(new Action(() =>
                    {
                        SetBusy(false);
                        MessageBox.Show(this, ex.Message, "خطأ في الإزالة", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }));
                }
            });
            t.IsBackground = true;
            t.Start();
        }
    }

    public class RoundPanel : Panel
    {
        public Color Fill = Ui.Card;
        public Color Border = Color.Empty;
        public int Radius = 12;
        public RoundPanel()
        {
            SetStyle(ControlStyles.UserPaint | ControlStyles.AllPaintingInWmPaint
                     | ControlStyles.OptimizedDoubleBuffer | ControlStyles.SupportsTransparentBackColor, true);
            BackColor = Color.Transparent;
        }
        protected override void OnPaint(PaintEventArgs e)
        {
            var g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            var r = new Rectangle(0, 0, Width - 1, Height - 1);
            using (var path = Ui.Round(r, Radius))
            using (var b = new SolidBrush(Fill))
            {
                g.FillPath(b, path);
                if (Border != Color.Empty) using (var pen = new Pen(Border, 1f)) g.DrawPath(pen, path);
            }
        }
    }
}
