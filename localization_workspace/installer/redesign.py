"""Redesign the installer window: official logo, key-art backdrop, logo palette, Ko-fi link.

Palette sampled from T_UI_MS2_Logo_White: steel #BACCD5 (lettering), red #BE0000 (the II).
Primary action = red, secondary = outlined steel, text/accents = steel. No gold anywhere.

Lessons from the first build (seen on a 4K screen):
  - custom OnPaintBackground + transparent child controls => WinForms ghosting. The backdrop
    (key art + gradient + hairline) is therefore BAKED into one image and set as the form's
    BackgroundImage, exactly like a solid colour would be. No custom background painting.
  - WinForms does not scale fixed pixel layouts under PerMonitorV2: AutoScaleMode.Dpi with a
    96-dpi baseline scales positions, sizes and the rounded Region together.
  - GDI+ measures Arabic tight: every label gets ~25% more height than the Latin default.
"""
import io, sys, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ---- bake the backdrop (2x for crispness on high-DPI) ----------------------
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
W, H = 1120, 1560
hero = Image.open(r"C:\Program Files (x86)\Steam\appcache\librarycache\2584270\6797ef35ca25b0f2876c8a16bc5f8deffa19dbe1\library_hero.jpg").convert("RGB")
hw, hh = hero.size
art = hero.crop((int(hw * 0.28), 0, int(hw * 0.72), hh)).resize((W, H))
art = ImageEnhance.Color(art).enhance(0.25)
art = ImageEnhance.Brightness(art).enhance(0.30)
art = art.filter(ImageFilter.GaussianBlur(1.5)).convert("RGBA")
base = Image.new("RGBA", (W, H), (16, 18, 20, 255))
art.putalpha(128)                                 # ~0.5 opacity over the base
base.alpha_composite(art)
grad = Image.new("RGBA", (W, H))
gd = ImageDraw.Draw(grad)
for y in range(H):
    t = y / (H - 1)
    a = int(40 + (246 - 40) * (t ** 1.15))        # darker towards the bottom
    gd.line([(0, y), (W, y)], fill=(16, 18, 20, a))
base.alpha_composite(grad)
# steel hairline above the Ko-fi row (y = 656 @1x)
hl = Image.new("RGBA", (W, H))
hd = ImageDraw.Draw(hl)
for x in range(80, W - 80):
    t = (x - 80) / (W - 160)
    a = int(120 * (1 - abs(t - 0.5) * 2))
    hd.line([(x, 656 * 2), (x, 656 * 2 + 1)], fill=(186, 204, 213, a))
base.alpha_composite(hl)
os.makedirs("ui", exist_ok=True)
base.convert("RGB").save("ui/ui_bg.jpg", quality=86, optimize=True)
print("ui_bg.jpg baked", base.size, os.path.getsize("ui/ui_bg.jpg") // 1024, "KB")

s = open("Program.cs", encoding="utf-8").read()

# ---- palette -------------------------------------------------------------
PAL = {
 "Bg = Color.FromArgb(30, 26, 23)":        "Bg = Color.FromArgb(16, 18, 20)",
 "Card = Color.FromArgb(44, 38, 33)":      "Card = Color.FromArgb(30, 34, 38)",
 "Gold = Color.FromArgb(206, 167, 92)":    "Gold = Color.FromArgb(186, 204, 213)   /* steel: logo lettering */",
 "GoldHover = Color.FromArgb(224, 187, 112)": "GoldHover = Color.FromArgb(211, 225, 232)",
 "Red = Color.FromArgb(168, 70, 58)":      "Red = Color.FromArgb(190, 0, 0)        /* the II */",
 "RedHover = Color.FromArgb(192, 86, 72)": "RedHover = Color.FromArgb(214, 24, 24)",
 "Ink = Color.FromArgb(34, 28, 23)":       "Ink = Color.FromArgb(12, 13, 15)",
 "Text = Color.FromArgb(236, 228, 214)":   "Text = Color.FromArgb(226, 232, 236)",
 "Muted = Color.FromArgb(150, 140, 128)":  "Muted = Color.FromArgb(128, 140, 148)",
}
for a, b in PAL.items():
    assert a in s, a
    s = s.replace(a, b)

# ---- helpers ---------------------------------------------------------------
s = s.replace("        public static Image LoadLogo()", '''        public static Image LoadBackground()
        {
            try
            {
                using (Stream st = Assembly.GetExecutingAssembly().GetManifestResourceStream("ui_bg.jpg"))
                using (var img = Image.FromStream(st))
                    return new Bitmap(img);
            }
            catch { return null; }
        }

        public static Image LoadLogo()''')
s = s.replace("        public int Radius = 14;\n        bool _hover;", "        public int Radius = 14;\n        public Color Outline = Color.Empty;\n        bool _hover;")
s = s.replace('''            using (var path = Ui.Round(rect, Radius))
            using (var b = new SolidBrush(fill))
                g.FillPath(b, path);
            var sf = new StringFormat''', '''            using (var path = Ui.Round(rect, Radius))
            using (var b = new SolidBrush(fill))
            {
                g.FillPath(b, path);
                if (Outline != Color.Empty) using (var pen = new Pen(Outline, 1f)) g.DrawPath(pen, path);
            }
            var sf = new StringFormat''')
s = s.replace("        public Color Fill = Ui.Card;\n        public int Radius = 12;", "        public Color Fill = Ui.Card;\n        public Color Border = Color.Empty;\n        public int Radius = 12;")
s = s.replace('''            using (var path = Ui.Round(r, Radius))
            using (var b = new SolidBrush(Fill))
                g.FillPath(b, path);
        }
    }
}''', '''            using (var path = Ui.Round(r, Radius))
            using (var b = new SolidBrush(Fill))
            {
                g.FillPath(b, path);
                if (Border != Color.Empty) using (var pen = new Pen(Border, 1f)) g.DrawPath(pen, path);
            }
        }
    }
}''')

# ---- border paint radius + DPI-safe rounded region ------------------------
s = s.replace('''        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            // subtle gold border
            using (var pen = new Pen(Color.FromArgb(60, Ui.Gold), 1))
            using (var path = Ui.Round(new Rectangle(0, 0, Width - 1, Height - 1), 18))''', '''        protected override void OnSizeChanged(EventArgs e)
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
            using (var path = Ui.Round(new Rectangle(0, 0, Width - 1, Height - 1), (int)(20 * DeviceDpi / 96f)))''')

# ---- constructor UI ------------------------------------------------------
start = s.index("        public MainForm()\n        {") + len("        public MainForm()\n        {")
end = s.index("            gamePath = Program.DetectGamePath();")
UI = '''
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

'''
s = s[:start] + UI + s[end:]
s = s.replace("Color.FromArgb(120, 170, 220)", "Ui.Gold")
s = s.replace('if (p != null && p.Length > 52) return "…" + p.Substring(p.Length - 50);', 'if (p != null && p.Length > 30) p = "…" + p.Substring(p.Length - 28); return p == null ? null : "\u202A" + p + "\u202C";')   # progress colour -> steel

assert "ko-fi.com/kindiboy" in s and "ui_bg.jpg" in s and s.count("OnPaintBackground") == 1
open("Program.cs", "w", encoding="utf-8").write(s)

c = open("ArabicInstaller.csproj", encoding="utf-8").read()
if "ui_bg.jpg" not in c:
    c = c.replace('<EmbeddedResource Include="ui\\ui_font.ttf"><LogicalName>ui_font.ttf</LogicalName></EmbeddedResource>',
                  '<EmbeddedResource Include="ui\\ui_font.ttf"><LogicalName>ui_font.ttf</LogicalName></EmbeddedResource>\n'
                  '    <EmbeddedResource Include="ui\\ui_bg.jpg"><LogicalName>ui_bg.jpg</LogicalName></EmbeddedResource>')
    open("ArabicInstaller.csproj", "w", encoding="utf-8").write(c)
print("redesign applied:", len(s.splitlines()), "lines")
