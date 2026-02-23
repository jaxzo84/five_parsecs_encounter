"""
Five Parsecs from Home — Encounter Sheet PDF Generator
=======================================================
Run alongside the encounter generator HTML.
Receives encounter JSON and returns a printable PDF.

Usage:
    python encounter_pdf_server.py

HTML posts to http://localhost:5679/pdf
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import io
import sys

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white, black, Color
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import Table, TableStyle
except ImportError:
    print("ERROR: reportlab not installed.  pip install reportlab")
    sys.exit(1)

# ── Palette ────────────────────────────────────────────────────────
BG      = HexColor('#0d0f14')
SURF    = HexColor('#13161e')
SURF2   = HexColor('#1c2030')
BORDER  = HexColor('#2a3045')
GOLD    = HexColor('#d4a84b')
GOLD2   = HexColor('#e8c06a')
TEAL    = HexColor('#2e7d7a')
TEAL2   = HexColor('#5ab8b4')
RED2    = HexColor('#c0392b')
TEXT    = HexColor('#d8dce8')
TEXT2   = HexColor('#8a90a8')
TEXT3   = HexColor('#5a6080')
DARK    = HexColor('#0d0f14')


def pt(mm_val):
    return mm_val * mm


def clamp_text(s, maxlen=60):
    s = str(s or '')
    return s[:maxlen] + ('…' if len(s) > maxlen else '')


def make_encounter_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    W, H = A4
    c = rl_canvas.Canvas(buf, pagesize=A4)

    def full_bg():
        c.setFillColor(BG)
        c.rect(0, 0, W, H, fill=1, stroke=0)

    def gold_line(x1, y1, x2, y2, w=0.5):
        c.setStrokeColor(GOLD)
        c.setLineWidth(w)
        c.line(x1, y1, x2, y2)

    def border_line(x1, y1, x2, y2, w=0.3):
        c.setStrokeColor(BORDER)
        c.setLineWidth(w)
        c.line(x1, y1, x2, y2)

    def box(x, y, bw, bh, title='', fill=SURF, title_fill=SURF2):
        c.setFillColor(fill)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.4)
        c.rect(x, y, bw, bh, fill=1, stroke=1)
        if title:
            c.setFillColor(title_fill)
            c.rect(x, y + bh - pt(5.5), bw, pt(5.5), fill=1, stroke=0)
            c.setFont('Helvetica-Bold', 6)
            c.setFillColor(GOLD)
            c.drawString(x + pt(2), y + bh - pt(3.8), title.upper())

    def label(txt, x, y, color=TEXT3, size=5.5):
        c.setFont('Helvetica', size)
        c.setFillColor(color)
        c.drawString(x, y, txt.upper())

    def value(txt, x, y, color=TEXT, size=9, bold=False):
        c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        c.setFillColor(color)
        c.drawString(x, y, str(txt))

    def stat_box(x, y, bw, bh, lbl, val, val_color=GOLD):
        c.setFillColor(BG)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.3)
        c.rect(x, y, bw, bh, fill=1, stroke=1)
        c.setFont('Helvetica', 5)
        c.setFillColor(TEXT3)
        c.drawCentredString(x + bw / 2, y + bh - pt(2.2), lbl.upper())
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(val_color)
        c.drawCentredString(x + bw / 2, y + pt(1.5), str(val))

    def multiline(txt, x, y, max_w, line_h=pt(4), size=7, color=TEXT2, indent=0):
        c.setFont('Helvetica', size)
        c.setFillColor(color)
        words = str(txt or '').split()
        line = ''
        cy = y
        for w in words:
            test = (line + ' ' + w).strip()
            if c.stringWidth(test, 'Helvetica', size) > max_w - indent:
                if line:
                    c.drawString(x + indent, cy, line)
                    cy -= line_h
                    indent = 0
                line = w
            else:
                line = test
        if line:
            c.drawString(x + indent, cy, line)
            cy -= line_h
        return cy

    # ── PAGE 1: ENCOUNTER SHEET ─────────────────────────────────────
    full_bg()

    # Header bar
    c.setFillColor(SURF)
    c.rect(0, H - pt(28), W, pt(28), fill=1, stroke=0)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.line(0, H - pt(28), W, H - pt(28))

    # Title
    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(GOLD)
    c.drawString(pt(12), H - pt(14), 'FIVE PARSECS FROM HOME')
    c.setFont('Helvetica', 7.5)
    c.setFillColor(TEXT3)
    c.drawString(pt(12), H - pt(21), 'ENCOUNTER SHEET  —  THIRD EDITION')

    # Mission type badge
    mission_map = {'opportunity': 'OPPORTUNITY MISSION', 'patron': 'PATRON MISSION',
                   'rival': 'RIVAL ATTACK', 'quest': 'QUEST MISSION', 'invasion': 'INVASION BATTLE'}
    mission_label = mission_map.get(data.get('mission', ''), data.get('mission', '').upper())
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(TEXT)
    c.drawRightString(W - pt(12), H - pt(13), mission_label)
    c.setFont('Helvetica', 6.5)
    c.setFillColor(TEXT3)
    diff = data.get('diff', 'normal').upper()
    crew = str(data.get('crewSize', 6))
    table_size = data.get('tableSize', '2.5x2.5')
    c.drawRightString(W - pt(12), H - pt(20.5), f'{diff} DIFFICULTY  ·  {crew}-FIGURE CREW  ·  {table_size} ft TABLE')

    # ── LAYOUT: two columns ─────────────────────────────────────────
    margin = pt(12)
    col_gap = pt(5)
    col_w = (W - 2 * margin - col_gap) / 2
    col1_x = margin
    col2_x = margin + col_w + col_gap
    y_start = H - pt(36)

    # ── ENEMY BLOCK ─────────────────────────────────────────────────
    enemy = data.get('enemy', {})
    ai_rules = {'A': 'Aggressive — charge nearest, cluster 1" apart',
                'C': 'Cautious — 2 groups, 6" apart, retreat to Cover',
                'D': 'Defensive — 3 teams 8" apart, hold and return fire',
                'G': 'Guardian — protect target, attack only if threatened',
                'R': 'Rampage — charge nearest, never retreat',
                'T': 'Tactical — 3 teams 8" apart, advance with Cover',
                'B': 'Beast — pairs spread across table, charge nearest prey'}

    enemy_bh = pt(74)
    box(col1_x, y_start - enemy_bh, col_w, enemy_bh, 'Enemy Force')
    ey = y_start - pt(10)

    # Name
    c.setFont('Helvetica-Bold', 13)
    c.setFillColor(TEXT)
    c.drawString(col1_x + pt(2), ey, str(enemy.get('name', '—')))
    ey -= pt(5)
    c.setFont('Helvetica', 6)
    c.setFillColor(TEAL2)
    c.drawString(col1_x + pt(2), ey, str(data.get('catDisplay', '')).upper())
    ey -= pt(7)

    # Stats row
    stat_labels = ['Speed', 'Combat', 'Toughness', 'AI', 'Panic']
    stat_vals = [enemy.get('speed', '—'), enemy.get('combat', '—'), enemy.get('tough', '—'),
                 f"{enemy.get('ai', '?')} — {ai_rules.get(enemy.get('ai', '?'), '?')[:16]}",
                 str(enemy.get('panic', '—'))]
    sw = col_w / 5
    for i, (sl, sv) in enumerate(zip(stat_labels, stat_vals)):
        stat_box(col1_x + i * sw, ey - pt(9.5), sw - pt(0.5), pt(10), sl, sv[:14])
    ey -= pt(12)

    # Composition row
    num_opp = data.get('numOpponents', 0)
    specs = data.get('specialists', 0)
    lt_present = data.get('hasLieutenant', False)
    ui_present = data.get('ui') is not None

    c.setFont('Helvetica', 6)
    c.setFillColor(TEXT3)
    c.drawString(col1_x + pt(2), ey, 'TOTAL OPPONENTS')
    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(GOLD)
    c.drawString(col1_x + pt(36), ey, str(num_opp))
    c.setFont('Helvetica', 6)
    c.setFillColor(TEXT2)
    c.drawString(col1_x + pt(46), ey, f'  {specs} SPECIALIST{"S" if specs != 1 else ""}')
    ey -= pt(4.5)

    if lt_present:
        c.setFont('Helvetica', 6.5)
        c.setFillColor(GOLD2)
        c.drawString(col1_x + pt(2), ey, '★ Lieutenant: +1 Combat Skill, carries Blade, Fearless')
    ey -= pt(4.5)

    # Weapons
    main_wpn = data.get('mainWeapon', '—')
    spec_wpn = data.get('specWeapon', '')
    ab = data.get('aggressiveBlade', '') or data.get('psychoBlade', '')
    c.setFont('Helvetica', 6)
    c.setFillColor(TEXT3)
    c.drawString(col1_x + pt(2), ey, 'STANDARD WEAPON:')
    c.setFont('Helvetica-Bold', 7.5)
    c.setFillColor(TEXT)
    c.drawString(col1_x + pt(33), ey, f'{main_wpn}{ab}')
    ey -= pt(4.5)
    if spec_wpn:
        c.setFont('Helvetica', 6)
        c.setFillColor(TEXT3)
        c.drawString(col1_x + pt(2), ey, 'SPECIALIST WEAPON:')
        c.setFont('Helvetica-Bold', 7.5)
        c.setFillColor(TEXT)
        c.drawString(col1_x + pt(33), ey, spec_wpn)
        ey -= pt(4.5)

    # Special rules
    border_line(col1_x + pt(1), ey + pt(1), col1_x + col_w - pt(1), ey + pt(1))
    ey -= pt(3)
    special = str(enemy.get('special', '') or '').replace('\\n', '\n')
    for line in special.split('\n')[:5]:
        line = line.strip()
        if not line:
            continue
        c.setFont('Helvetica', 5.5)
        c.setFillColor(GOLD2)
        c.drawString(col1_x + pt(2), ey, line[:85])
        ey -= pt(3.5)

    # ── UNIQUE INDIVIDUAL (right column top) ─────────────────────────
    ui = data.get('ui')
    ui_bh = pt(40) if ui else pt(0)
    right_y = y_start

    if ui:
        box(col2_x, right_y - ui_bh, col_w, ui_bh, 'Unique Individual (additional figure)', title_fill=HexColor('#2a2010'))
        uy = right_y - pt(10)
        c.setFont('Helvetica-Bold', 11)
        c.setFillColor(GOLD2)
        c.drawString(col2_x + pt(2), uy, str(ui.get('name', '?')))
        uy -= pt(5)
        ui_stat_labels = ['Speed', 'Combat', 'Tough', 'AI', 'Luck']
        ui_stat_vals = [ui.get('speed', '—'), ui.get('combat', '—'), ui.get('tough', '—'),
                        ui.get('ai', '—'), str(ui.get('luck', 0))]
        sw2 = col_w / 5
        for i, (sl, sv) in enumerate(zip(ui_stat_labels, ui_stat_vals)):
            stat_box(col2_x + i * sw2, uy - pt(9), sw2 - pt(0.5), pt(9.5), sl, sv[:10], GOLD2)
        uy -= pt(12)
        c.setFont('Helvetica', 6)
        c.setFillColor(TEXT3)
        c.drawString(col2_x + pt(2), uy, 'WEAPON:')
        c.setFont('Helvetica-Bold', 7)
        c.setFillColor(TEXT)
        c.drawString(col2_x + pt(16), uy, str(ui.get('wpn', '—')))
        uy -= pt(4)
        ui_spec = str(ui.get('special', '') or '')
        for line in ui_spec.split('\n')[:3]:
            c.setFont('Helvetica', 5.5)
            c.setFillColor(TEXT2)
            c.drawString(col2_x + pt(2), uy, line[:70])
            uy -= pt(3.5)
        right_y -= ui_bh

    # ── MISSION SETUP (right column) ─────────────────────────────────
    setup_bh = pt(74) - ui_bh
    box(col2_x, y_start - pt(74), col_w, setup_bh, 'Mission Setup')

    sy = right_y - pt(8)

    # Objective
    obj = data.get('objective') or data.get('rivalAttack')
    if obj:
        c.setFont('Helvetica-Bold', 9)
        c.setFillColor(TEAL2)
        c.drawString(col2_x + pt(2), sy, f"OBJECTIVE: {str(obj.get('name', '?')).upper()}")
        sy -= pt(4)
        sy = multiline(obj.get('desc', ''), col2_x + pt(2), sy, col_w - pt(4), pt(3.8), 6.5)
        sy -= pt(2)

    border_line(col2_x + pt(1), sy + pt(0.5), col2_x + col_w - pt(1), sy + pt(0.5))
    sy -= pt(3)

    # Deployment condition
    dep = data.get('depCondition', {})
    c.setFont('Helvetica-Bold', 7.5)
    c.setFillColor(RED2)
    c.drawString(col2_x + pt(2), sy, f"DEPLOY: {str(dep.get('name', 'No Condition')).upper()}")
    sy -= pt(4)
    if dep.get('desc'):
        sy = multiline(dep.get('desc', ''), col2_x + pt(2), sy, col_w - pt(4), pt(3.5), 6)
    sy -= pt(2)

    border_line(col2_x + pt(1), sy + pt(0.5), col2_x + col_w - pt(1), sy + pt(0.5))
    sy -= pt(3)

    # Notable sight
    sight = data.get('sight', {})
    sname = str(sight.get('name', '') or '')
    if sname and sname not in ('Nothing Special', 'Invasion — No Notable Sight'):
        c.setFont('Helvetica-Bold', 7.5)
        c.setFillColor(GOLD)
        c.drawString(col2_x + pt(2), sy, f"SIGHT: {sname.upper()}")
        sy -= pt(4)
        sy = multiline(sight.get('desc', ''), col2_x + pt(2), sy, col_w - pt(4), pt(3.5), 6)
    else:
        c.setFont('Helvetica', 7)
        c.setFillColor(TEXT3)
        c.drawString(col2_x + pt(2), sy, 'NOTABLE SIGHT: Nothing special.')
    sy -= pt(2)

    # ── LOWER SECTION (full width) ────────────────────────────────────
    lower_y = y_start - pt(80)

    # Terrain + Patron side by side
    terrain_bh = pt(30)
    tbox_w = (W - 2 * margin - col_gap) / 2
    box(col1_x, lower_y - terrain_bh, tbox_w, terrain_bh, 'Terrain Setup')

    terrain = data.get('terrain', {})
    ty = lower_y - pt(10)
    t_items = [('Large features', terrain.get('large', 0), 'Fill sector. Obstruct sight, provide cover.'),
               ('Small features', terrain.get('small', 0), 'Clusters. Provide cover.'),
               ('Linear features', terrain.get('linear', 0), '4–8" long. Block LOS, provide cover.')]
    for tname, tcount, tdesc in t_items:
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(GOLD)
        c.drawString(col1_x + pt(2), ty, str(tcount))
        c.setFont('Helvetica-Bold', 7)
        c.setFillColor(TEXT)
        c.drawString(col1_x + pt(8), ty, tname)
        c.setFont('Helvetica', 5.5)
        c.setFillColor(TEXT3)
        c.drawString(col1_x + pt(8), ty - pt(3), tdesc)
        ty -= pt(7.5)

    # Patron details (if present)
    pd = data.get('patronDetails')
    if pd:
        box(col2_x, lower_y - terrain_bh, tbox_w, terrain_bh, 'Patron Job Details')
        pty = lower_y - pt(10)
        c.setFont('Helvetica', 6)
        c.setFillColor(TEXT3)
        c.drawString(col2_x + pt(2), pty, 'DANGER PAY:')
        c.setFont('Helvetica-Bold', 7)
        c.setFillColor(GOLD)
        c.drawString(col2_x + pt(22), pty, str(pd.get('dangerPay', {}).get('val', '—')))
        pty -= pt(4.5)
        c.setFont('Helvetica', 6)
        c.setFillColor(TEXT3)
        c.drawString(col2_x + pt(2), pty, 'TIME FRAME:')
        c.setFont('Helvetica', 7)
        c.setFillColor(TEXT)
        c.drawString(col2_x + pt(22), pty, str(pd.get('timeFrame', '—'))[:38])
        pty -= pt(4.5)
        for label_txt, val_dict, col in [
            ('Benefit', pd.get('benefit'), TEAL2),
            ('Hazard', pd.get('hazard'), RED2),
            ('Condition', pd.get('condition'), GOLD2),
        ]:
            if val_dict:
                c.setFont('Helvetica-Bold', 6)
                c.setFillColor(col)
                c.drawString(col2_x + pt(2), pty, f"{label_txt.upper()}: {val_dict.get('name','')}")
                c.setFont('Helvetica', 5.5)
                c.setFillColor(TEXT2)
                c.drawString(col2_x + pt(2), pty - pt(3), str(val_dict.get('effect', ''))[:65])
                pty -= pt(7)
    else:
        # AI Reference box
        box(col2_x, lower_y - terrain_bh, tbox_w, terrain_bh, 'AI Reference')
        ay = lower_y - pt(10)
        ai_code = str(enemy.get('ai', 'A'))
        ai_full = ai_rules.get(ai_code, '—')
        c.setFont('Helvetica-Bold', 9)
        c.setFillColor(TEAL2)
        c.drawString(col2_x + pt(2), ay, ai_full[:50])
        ay -= pt(5)
        deploy_notes = {
            'A': "Set up in 1 cluster, 1\" between figures. Charge nearest enemy each turn.",
            'R': "Same as Aggressive. Will never retreat from combat.",
            'C': "2 groups, 6\" apart. Prefer Cover. Retreat if exposed.",
            'D': "3 teams, 8\" apart. Hold positions. Return fire.",
            'T': "3 teams, 8\" apart. Advance using Cover. Prioritize objectives.",
            'G': "Stay within 8\" of assigned target. Only engage direct threats.",
            'B': "Pairs spread across table in 3 zones. 2\" between pair. Hunt nearest prey.",
        }
        c.setFont('Helvetica', 6.5)
        c.setFillColor(TEXT2)
        note = deploy_notes.get(ai_code, '')
        for chunk in [note[i:i+60] for i in range(0, len(note), 60)]:
            c.drawString(col2_x + pt(2), ay, chunk)
            ay -= pt(4)

    # ── BATTLE REFERENCE STRIP ─────────────────────────────────────
    ref_y = lower_y - terrain_bh - pt(4)
    ref_h = pt(48)
    box(col1_x, ref_y - ref_h, W - 2 * margin, ref_h, 'Battle Round Reference')

    rx = col1_x + pt(2)
    ry = ref_y - pt(10)
    rw = (W - 2 * margin - pt(6)) / 3

    # Column 1: Round sequence
    c.setFont('Helvetica-Bold', 6.5)
    c.setFillColor(GOLD)
    c.drawString(rx, ry, 'ROUND SEQUENCE')
    ry2 = ry - pt(4)
    seq = ['1. Reaction Roll — roll Xd6, assign to crew', '2. Quick Actions — die ≤ Reactions score',
           '3. Enemy Actions — closest to your edge first', '4. Slow Actions — remaining crew',
           '5. End Phase — Morale, objectives, events']
    for s in seq:
        c.setFont('Helvetica', 6)
        c.setFillColor(TEXT2)
        c.drawString(rx, ry2, s)
        ry2 -= pt(3.8)

    # Column 2: Initiative / Seize
    rx2 = rx + rw + pt(3)
    ry3 = ry
    c.setFont('Helvetica-Bold', 6.5)
    c.setFillColor(GOLD)
    c.drawString(rx2, ry3, 'SEIZE THE INITIATIVE')
    ry3 -= pt(4)
    seize_lines = [
        'Roll 2D6 + highest crew Savvy.',
        '+1 if outnumbered.',
        f'-1 if facing Hired Muscle.',
        '10+: Each crew may Move or Fire',
        '    before Round 1 begins.',
        '    (Shots only hit on natural 6.)',
    ]
    for sl in seize_lines:
        c.setFont('Helvetica', 6)
        c.setFillColor(TEXT2)
        c.drawString(rx2, ry3, sl)
        ry3 -= pt(3.8)

    # Column 3: Morale
    rx3 = rx2 + rw + pt(3)
    ry4 = ry
    c.setFont('Helvetica-Bold', 6.5)
    c.setFillColor(GOLD)
    c.drawString(rx3, ry4, 'ENEMY MORALE')
    ry4 -= pt(4)
    panic_range = str(enemy.get('panic', '1'))
    morale_lines = [
        f"Panic range: {panic_range}",
        'At end of each round:',
        '  Roll 1D6 per casualty this round.',
        '  Each die in panic range = 1 Bail.',
        '  Apply from closest to their edge.',
        '  Panic 0 = fight to the death.',
    ]
    for ml in morale_lines:
        c.setFont('Helvetica', 6)
        c.setFillColor(TEXT2)
        if ml.startswith('Panic range'):
            c.setFillColor(GOLD2)
        c.drawString(rx3, ry4, ml)
        ry4 -= pt(3.8)

    # ── PAGE FOOTER ─────────────────────────────────────────────────
    c.setFont('Helvetica', 5.5)
    c.setFillColor(TEXT3)
    c.drawCentredString(W / 2, pt(8),
        'Five Parsecs from Home Third Edition  ·  Permission is granted to copy for personal use.')

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f'  {self.address_string()} — {fmt % args}')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path != '/pdf':
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
            pdf_bytes = make_encounter_pdf(data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', 'attachment; filename="encounter.pdf"')
            self.send_header('Content-Length', str(len(pdf_bytes)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(pdf_bytes)
            enemy_name = data.get('enemy', {}).get('name', 'unknown')
            print(f'  ✓ Encounter PDF generated ({len(pdf_bytes):,} bytes) — {enemy_name}')
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_error(500, str(e))


if __name__ == '__main__':
    host, port = '127.0.0.1', 5679
    server = HTTPServer((host, port), Handler)
    print('┌──────────────────────────────────────────────────────────┐')
    print('│  Five Parsecs from Home — Encounter PDF Server          │')
    print(f'│  Listening on http://{host}:{port}                   │')
    print('│  Open index.html in your browser, generate encounter,  │')
    print('│  then click Print PDF.                                  │')
    print('│  Press Ctrl+C to stop.                                  │')
    print('└──────────────────────────────────────────────────────────┘')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
