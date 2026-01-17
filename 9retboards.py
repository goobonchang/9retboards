import tkinter as tk
from tkinter import ttk


class Fretboard12Proto1:
    def __init__(self, root):
        self.root = root
        self.root.title("Fretboard Proto 1")

        # ===== Settings =====
        self.max_fret = 12
        self.strings = 6

        self.margin = 20
        self.board_w = 1100
        self.board_h = 260
        self.open_w = 80

        self.outer_pad_y = 40
        self.extend_out = 22

        # 1번줄(위) -> 6번줄(아래): E, B, G, D, A, E
        self.open_pc = [4, 11, 7, 2, 9, 4]

        self.note_sharp = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.note_flat  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

        # 수동 클릭(같은 음 전체 토글)
        self.active_points = set()

        # 스케일 자동 표시
        self.scale_points = set()
        self.scale_allowed_pcs = set()

        # 코드 자동 표시
        self.chord_allowed_pcs = set()
        self.chord_points = set()

        # ===== Scale/Chord Library =====
        self.scale_defs = self.build_scale_library()
        self.triad_defs = self.build_triad_library()
        self.tension_defs = self.build_tension_library()
        self.inversion_defs = self.build_inversion_library()

        # ===== Recommended chord-form groups (색) =====
        # 여기서 "1번폼=빨강, 2번폼=파랑..."을 정의하고,
        # chord_points를 "폼 그룹"으로 나눠서 색을 다르게 칠함.
        self.form_groups = self.build_recommended_form_groups()

        # ===== Canvas =====
        self.canvas = tk.Canvas(
            root,
            width=self.board_w + self.open_w + self.margin * 2,
            height=self.board_h + self.outer_pad_y * 2 + self.margin * 2 + 30,
            bg="white",
            highlightthickness=0
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        self.build_bottom_ui(root)

        # 초기 상태
        self.tonic_pc = self.key_item_to_pc(self.key_var.get())

        # 초기: 스케일 없음
        self.apply_selected_scale()

        # 초기: 코드 없음
        self.apply_selected_chord()

        self.draw()

    # =========================
    # UI
    # =========================
    def build_bottom_ui(self, root):
        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=10, pady=(6, 10))

        row1 = tk.Frame(bottom)
        row1.pack(fill="x")

        tk.Label(row1, text="Key").pack(side="left")
        self.key_items = [
            "C (Am)", "G (Em)", "D (Bm)", "A (F#m)", "E (C#m)", "B (G#m)",
            "F# / Gb (D#m / Ebm)", "Db / C# (Bbm / A#m)", "Ab / G# (Fm)",
            "Eb / D# (Cm)", "Bb / A# (Gm)", "F (Dm)"
        ]
        self.key_var = tk.StringVar(value=self.key_items[0])

        self.key_combo = ttk.Combobox(row1, values=self.key_items, textvariable=self.key_var,
                                      state="readonly", width=18)
        self.key_combo.pack(side="left", padx=(8, 12))
        self.key_combo.bind("<<ComboboxSelected>>", self.on_key_changed)

        tk.Label(row1, text="Scale").pack(side="left")
        scale_names = list(self.scale_defs.keys())
        self.scale_items = ["(없음)"] + scale_names
        self.scale_var = tk.StringVar(value="(없음)")

        self.scale_combo = ttk.Combobox(row1, values=self.scale_items, textvariable=self.scale_var,
                                        state="readonly", width=30)
        self.scale_combo.pack(side="left", padx=(8, 12))
        self.scale_combo.bind("<<ComboboxSelected>>", self.on_scale_changed)

        self.key_hint = tk.Label(row1, fg="gray")
        self.key_hint.pack(side="left", padx=(0, 12))

        self.scale_hint = tk.Label(row1, text="스케일: 없음", fg="gray", wraplength=520, justify="left")
        self.scale_hint.pack(side="left", padx=(0, 12))

        # Row 2: Chord
        row2 = tk.Frame(bottom)
        row2.pack(fill="x", pady=(6, 0))

        tk.Label(row2, text="Chord").pack(side="left")

        tk.Label(row2, text="Triad").pack(side="left", padx=(8, 0))
        self.triad_items = ["(없음)"] + list(self.triad_defs.keys())
        self.triad_var = tk.StringVar(value="(없음)")
        self.triad_combo = ttk.Combobox(row2, values=self.triad_items, textvariable=self.triad_var,
                                        state="readonly", width=10)
        self.triad_combo.pack(side="left", padx=(6, 12))
        self.triad_combo.bind("<<ComboboxSelected>>", self.on_chord_changed)

        tk.Label(row2, text="Tension").pack(side="left")
        self.tension_items = ["(없음)"] + list(self.tension_defs.keys())
        self.tension_var = tk.StringVar(value="(없음)")
        self.tension_combo = ttk.Combobox(row2, values=self.tension_items, textvariable=self.tension_var,
                                          state="readonly", width=18)
        self.tension_combo.pack(side="left", padx=(6, 12))
        self.tension_combo.bind("<<ComboboxSelected>>", self.on_chord_changed)

        tk.Label(row2, text="Inversion").pack(side="left")
        self.inversion_items = list(self.inversion_defs.keys())
        self.inversion_var = tk.StringVar(value="Root")
        self.inversion_combo = ttk.Combobox(row2, values=self.inversion_items, textvariable=self.inversion_var,
                                            state="readonly", width=10)
        self.inversion_combo.pack(side="left", padx=(6, 12))
        self.inversion_combo.bind("<<ComboboxSelected>>", self.on_chord_changed)

        tk.Label(row2, text="Form").pack(side="left")
        self.form_items = ["(전체)"] + list(self.form_groups.keys())
        self.form_var = tk.StringVar(value="(전체)")
        self.form_combo = ttk.Combobox(row2, values=self.form_items, textvariable=self.form_var,
                                       state="readonly", width=14)
        self.form_combo.pack(side="left", padx=(6, 12))
        self.form_combo.bind("<<ComboboxSelected>>", self.on_form_changed)

        self.chord_hint = tk.Label(row2, text="코드: -", fg="gray", wraplength=900, justify="left")
        self.chord_hint.pack(side="left", padx=(0, 12))

        row3 = tk.Frame(bottom)
        row3.pack(fill="x", pady=(6, 0))
        self.click_info = tk.Label(row3, text="클릭: -")
        self.click_info.pack(side="left")

        self.update_key_hint()

    # =========================
    # Events
    # =========================
    def on_key_changed(self, _=None):
        self.tonic_pc = self.key_item_to_pc(self.key_var.get())
        self.active_points.clear()
        self.update_key_hint()
        self.click_info.config(text="클릭: -")
        self.apply_selected_scale()
        self.apply_selected_chord()
        self.draw()

    def on_scale_changed(self, _=None):
        self.apply_selected_scale()
        self.draw()

    def on_chord_changed(self, _=None):
        self.apply_selected_chord()
        self.draw()

    def on_form_changed(self, _=None):
        self.draw()

    def update_key_hint(self):
        item = self.key_var.get()
        if "(" in item and ")" in item:
            major = item.split("(")[0].strip()
            minor = item.split("(")[1].split(")")[0].strip()
            self.key_hint.config(text=f"선택: {major}   나란한조: {minor}")
        else:
            self.key_hint.config(text=f"선택: {item}")

    # =========================
    # Libraries
    # =========================
    def build_scale_library(self):
        lib = {}
        lib["Major (Ionian)"] = [0,2,4,5,7,9,11]
        lib["Dorian"] = [0,2,3,5,7,9,10]
        lib["Phrygian"] = [0,1,3,5,7,8,10]
        lib["Lydian"] = [0,2,4,6,7,9,11]
        lib["Mixolydian"] = [0,2,4,5,7,9,10]
        lib["Natural Minor (Aeolian)"] = [0,2,3,5,7,8,10]
        lib["Locrian"] = [0,1,3,5,6,8,10]
        lib["Harmonic Minor"] = [0,2,3,5,7,8,11]
        lib["Melodic Minor (Asc)"] = [0,2,3,5,7,9,11]
        lib["Lydian Dominant"] = [0,2,4,6,7,9,10]
        lib["Mixolydian b6"] = [0,2,4,5,7,8,10]
        lib["Locrian #2"] = [0,2,3,5,6,8,10]
        lib["Altered (Super Locrian)"] = [0,1,3,4,6,8,10]
        for k in list(lib.keys()):
            lib[k] = sorted(set([x % 12 for x in lib[k]]))
        return lib

    def build_triad_library(self):
        return {
            "M": [0, 4, 7],
            "m": [0, 3, 7],
            "dim": [0, 3, 6],
            "aug": [0, 4, 8],
            "sus2": [0, 2, 7],
            "sus4": [0, 5, 7],
            "5": [0, 7],
            "add9": [0, 4, 7, 2],
            "madd9": [0, 3, 7, 2],
        }

    def build_tension_library(self):
        return {
            "6": [9],
            "7": [10],
            "maj7": [11],
            "9": [2, 10],
            "maj9": [2, 11],
            "11": [5, 10],
            "13": [9, 10],
            "6/9": [2, 9],
            "7b9": [1, 10],
            "7#9": [3, 10],
            "7#11": [6, 10],
            "7b13": [8, 10],
            "alt (b9 #9 b5 #5)": [1, 3, 6, 8, 10],
        }

    def build_inversion_library(self):
        return {"Root": 0, "1st": 1, "2nd": 2, "3rd": 3}

    def build_recommended_form_groups(self):
        # “폼”을 실제 보이싱으로 만들려면(포지션/스트링 선택) 더 복잡해짐.
        # 지금 단계에서는 "추천 폼 그룹"을 단순히 색 그룹으로만 제공.
        # (전체) 선택 시: 모든 코드톤을 색으로 분류해서 보여줌.

        # 1번폼=빨강, 2번폼=파랑, 3번폼=초록, 4번폼=보라, 5번폼=주황
        # (사용자 요청대로 색 분류)
        return {
            "Form 1 (Red)": {"fill": "#d32f2f", "text": "white"},
            "Form 2 (Blue)": {"fill": "#1976d2", "text": "white"},
            "Form 3 (Green)": {"fill": "#388e3c", "text": "white"},
            "Form 4 (Purple)": {"fill": "#7b1fa2", "text": "white"},
            "Form 5 (Orange)": {"fill": "#f57c00", "text": "black"},
        }

    # =========================
    # Music helpers
    # =========================
    def note_name_to_pc(self, name: str) -> int:
        name = (name or "").strip()
        if not name:
            return 0
        base_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        base = base_map.get(name[0].upper(), 0)
        acc = name[1:].strip()
        if acc == "#":
            base += 1
        elif acc.lower() == "b":
            base -= 1
        return base % 12

    def key_item_to_pc(self, item: str) -> int:
        major_part = item.split("(")[0].strip()
        first_name = major_part.split("/")[0].strip()
        return self.note_name_to_pc(first_name)

    def pc_to_note_text(self, pc: int) -> str:
        ns = self.note_sharp[pc % 12]
        nf = self.note_flat[pc % 12]
        return f"{ns}/{nf}" if ns != nf else ns

    def tension_label(self, semis: int) -> str:
        return ["R", "b9", "9", "#9", "3", "11", "#11", "5", "b13", "13", "b7", "7"][semis % 12]

    # =========================
    # Apply scale
    # =========================
    def apply_selected_scale(self):
        name = self.scale_var.get()
        if name == "(없음)":
            self.scale_allowed_pcs = set()
            self.scale_points = set()
            self.scale_hint.config(text="스케일: 없음")
            return

        intervals = self.scale_defs.get(name, [])
        allowed = set((self.tonic_pc + i) % 12 for i in intervals)

        self.scale_allowed_pcs = allowed
        pts = set()
        for s in range(self.strings):
            for f in range(self.max_fret + 1):
                pc = (self.open_pc[s] + f) % 12
                if pc in allowed:
                    pts.add((s, f))
        self.scale_points = pts

        notes = [self.pc_to_note_text(pc) for pc in sorted(allowed)]
        note_text = ", ".join(notes)
        if len(note_text) > 60:
            note_text = note_text[:60] + "..."
        self.scale_hint.config(text=f"스케일: {name}   음: {note_text}")

    # =========================
    # Apply chord
    # =========================
    def apply_selected_chord(self):
        triad_name = self.triad_var.get()
        tension_name = self.tension_var.get()

        if triad_name == "(없음)":
            self.chord_allowed_pcs = set()
            self.chord_points = set()
            self.chord_hint.config(text="코드: -")
            return

        triad_intervals = self.triad_defs.get(triad_name, [0])
        extra = []
        if tension_name != "(없음)":
            extra = self.tension_defs.get(tension_name, [])

        intervals = sorted(set([i % 12 for i in (triad_intervals + extra)]))
        allowed = set((self.tonic_pc + i) % 12 for i in intervals)
        self.chord_allowed_pcs = allowed

        pts = set()
        for s in range(self.strings):
            for f in range(self.max_fret + 1):
                pc = (self.open_pc[s] + f) % 12
                if pc in allowed:
                    pts.add((s, f))
        self.chord_points = pts

        # chord name
        root_name = self.pc_to_note_text(self.tonic_pc)
        chord_name = root_name
        if triad_name == "m":
            chord_name += "m"
        elif triad_name not in ("M", "m"):
            chord_name += triad_name

        if tension_name != "(없음)":
            chord_name += tension_name

        # inversion display only
        inv_name = self.inversion_var.get()
        bass_pc = self.pick_bass_pc_for_inversion(inv_name)
        if bass_pc is not None and inv_name != "Root":
            chord_name += f"/{self.pc_to_note_text(bass_pc)}"

        notes = [self.pc_to_note_text(pc) for pc in sorted(allowed)]
        note_text = ", ".join(notes)
        if len(note_text) > 80:
            note_text = note_text[:80] + "..."
        self.chord_hint.config(text=f"코드: {chord_name}   음: {note_text}")

    def pick_bass_pc_for_inversion(self, inv_name: str):
        if not self.chord_allowed_pcs:
            return None
        inv_index = self.inversion_defs.get(inv_name, 0)
        rels = sorted(set((pc - self.tonic_pc) % 12 for pc in self.chord_allowed_pcs))
        if inv_index <= 0:
            return self.tonic_pc
        if inv_index >= len(rels):
            inv_index = len(rels) - 1
        return (self.tonic_pc + rels[inv_index]) % 12

    # =========================
    # Geometry
    # =========================
    def fret_positions(self, x0: float, width: float):
        L = 1.0
        ratios = [0.0] + [L - (L / (2 ** (n / 12))) for n in range(1, self.max_fret + 1)]
        r_last = ratios[-1]
        return [x0 + (r / r_last) * width for r in ratios]

    def fret_center_x(self, fret: int) -> float:
        if fret == 0:
            return self.x0 - self.open_w / 2
        return (self.fret_x[fret - 1] + self.fret_x[fret]) / 2

    def fret_cell_bounds_x(self, fret: int):
        if fret == 0:
            pad = 12
            left = self.x0 - self.open_w + pad
            right = self.x0 - pad
            return left, right
        return self.fret_x[fret - 1], self.fret_x[fret]

    def x_to_fret(self, x: float) -> int:
        if x < self.x0:
            return 0
        centers = [self.fret_center_x(f) for f in range(1, self.max_fret + 1)]
        return min(range(1, self.max_fret + 1), key=lambda f: abs(centers[f - 1] - x))

    def string_cell_bounds_y(self, s: int):
        inner_pad = 2
        max_cell_h = 40

        if s == 0:
            top0 = self.y0 - self.extend_out
            bottom0 = (self.string_y[0] + self.string_y[1]) / 2
        elif s == self.strings - 1:
            top0 = (self.string_y[self.strings - 2] + self.string_y[self.strings - 1]) / 2
            bottom0 = self.y1 + self.extend_out
        else:
            top0 = (self.string_y[s - 1] + self.string_y[s]) / 2
            bottom0 = (self.string_y[s] + self.string_y[s + 1]) / 2

        top = top0 + inner_pad
        bottom = bottom0 - inner_pad

        h = bottom - top
        if h > max_cell_h:
            mid = (top + bottom) / 2
            top = mid - max_cell_h / 2
            bottom = mid + max_cell_h / 2

        canvas_top = self.margin
        canvas_bottom = self.margin + self.outer_pad_y * 2 + self.board_h
        if top < canvas_top:
            top = canvas_top
        if bottom > canvas_bottom:
            bottom = canvas_bottom
        if bottom <= top + 10:
            bottom = top + 10

        return top, bottom

    # =========================
    # Draw
    # =========================
    def draw(self):
        self.canvas.delete("all")

        m = self.margin
        self.y0 = m + self.outer_pad_y
        self.y1 = self.y0 + self.board_h

        self.open_x0 = m
        self.x0 = m + self.open_w

        self.fret_x = self.fret_positions(self.x0, self.board_w)
        self.x1 = self.fret_x[-1]

        wood = "#8b5a2b"
        self.canvas.create_rectangle(self.x0, self.y0, self.x1, self.y1, fill=wood, outline="black", width=2)
        self.canvas.create_line(self.x0, self.y0, self.x0, self.y1, width=8)

        for i in range(1, self.max_fret + 1):
            self.canvas.create_line(self.fret_x[i], self.y0, self.fret_x[i], self.y1, width=3 if i == 12 else 2)

        self.string_y = []
        for s in range(self.strings):
            y = self.y0 + self.board_h * s / (self.strings - 1)
            self.string_y.append(y)
            self.canvas.create_line(self.x0, y, self.x1, y, width=s + 1)

        self.draw_inlays()
        self.draw_roots()
        self.draw_scale_cells()

        # 코드톤 표시: 선택한 "Form"에 따라 색으로 묶어서 그림
        self.draw_chord_cells_by_form()

        self.draw_active_cells()
        self.draw_fret_numbers()

    def draw_inlays(self):
        inlay_frets = [3, 5, 7, 9, 12]
        radius = 7
        center_y = (self.y0 + self.y1) / 2
        offset_12 = 48
        for f in inlay_frets:
            x_center = self.fret_center_x(f)
            if f == 12:
                self.canvas.create_oval(x_center - radius, center_y - offset_12 - radius,
                                        x_center + radius, center_y - offset_12 + radius,
                                        fill="ivory", outline="")
                self.canvas.create_oval(x_center - radius, center_y + offset_12 - radius,
                                        x_center + radius, center_y + offset_12 + radius,
                                        fill="ivory", outline="")
            else:
                self.canvas.create_oval(x_center - radius, center_y - radius,
                                        x_center + radius, center_y + radius,
                                        fill="ivory", outline="")

    def draw_fret_numbers(self):
        label_y = self.y1 + 14
        for f in [3, 5, 7, 9, 12]:
            self.canvas.create_text(self.fret_center_x(f), label_y, text=str(f), fill="black")

    def draw_roots(self):
        r = 12
        for s in range(self.strings):
            y = self.string_y[s]
            for fret in range(self.max_fret + 1):
                pc = (self.open_pc[s] + fret) % 12
                if pc != self.tonic_pc:
                    continue
                x = self.fret_center_x(fret)
                self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                        fill="white", outline="black", width=2)
                self.canvas.create_text(x, y + 0.5, text="R", fill="black",
                                        font=("Arial", 11, "bold"))

    def draw_scale_cells(self):
        if not self.scale_points:
            return
        for (s, fret) in self.scale_points:
            pc = (self.open_pc[s] + fret) % 12
            semis = (pc - self.tonic_pc) % 12
            tension = self.tension_label(semis)
            note_text = self.pc_to_note_text(pc)

            left, right = self.fret_cell_bounds_x(fret)
            top, bottom = self.string_cell_bounds_y(s)

            self.canvas.create_rectangle(left + 2, top + 1, right - 2, bottom - 1,
                                         fill="#555555", outline="black", width=1)
            cx = (left + right) / 2
            cy = (top + bottom) / 2
            self.canvas.create_text(cx, cy - 6, text=tension, fill="white", font=("Arial", 10, "bold"))
            self.canvas.create_text(cx, cy + 8, text=note_text, fill="white", font=("Arial", 8, "bold"))

    def chord_color_for_point(self, s: int, fret: int):
        # "추천 폼"은 원래 특정 보이싱(스트링/프렛 조합)이어야 하지만,
        # 지금은 단순히 “코드톤들”을 폼 그룹 색으로 묶어서 보여주는 단계.
        # (전체)일 때는 코드톤을 5개 그룹으로 “분산”해서 색이 섞여 보이도록 함.
        # 선택된 폼이 있으면 그 폼 색 하나로 통일.

        selected_form = self.form_var.get()
        if selected_form != "(전체)" and selected_form in self.form_groups:
            fg = self.form_groups[selected_form]
            return fg["fill"], fg["text"]

        # (전체)일 때: 위치 기반으로 그룹을 나눔(항상 같은 점은 항상 같은 색)
        # 그룹 인덱스 0~4
        idx = (s * 13 + fret) % 5
        key = list(self.form_groups.keys())[idx]
        fg = self.form_groups[key]
        return fg["fill"], fg["text"]

    def draw_chord_cells_by_form(self):
        if not self.chord_points:
            return

        for (s, fret) in self.chord_points:
            pc = (self.open_pc[s] + fret) % 12
            semis = (pc - self.tonic_pc) % 12
            tension = self.tension_label(semis)
            note_text = self.pc_to_note_text(pc)

            left, right = self.fret_cell_bounds_x(fret)
            top, bottom = self.string_cell_bounds_y(s)

            fill_color, text_color = self.chord_color_for_point(s, fret)

            self.canvas.create_rectangle(left + 2, top + 1, right - 2, bottom - 1,
                                         fill=fill_color, outline="black", width=2)
            cx = (left + right) / 2
            cy = (top + bottom) / 2
            self.canvas.create_text(cx, cy - 6, text=tension, fill=text_color, font=("Arial", 10, "bold"))
            self.canvas.create_text(cx, cy + 8, text=note_text, fill=text_color, font=("Arial", 8, "bold"))

    def draw_active_cells(self):
        for (s, fret) in self.active_points:
            pc = (self.open_pc[s] + fret) % 12
            semis = (pc - self.tonic_pc) % 12
            tension = self.tension_label(semis)
            note_text = self.pc_to_note_text(pc)

            left, right = self.fret_cell_bounds_x(fret)
            top, bottom = self.string_cell_bounds_y(s)

            self.canvas.create_rectangle(left + 2, top + 1, right - 2, bottom - 1,
                                         fill="#111111", outline="black", width=2)
            cx = (left + right) / 2
            cy = (top + bottom) / 2
            self.canvas.create_text(cx, cy - 6, text=tension, fill="white", font=("Arial", 10, "bold"))
            self.canvas.create_text(cx, cy + 8, text=note_text, fill="white", font=("Arial", 8, "bold"))

    # =========================
    # Click
    # =========================
    def points_for_pc(self, pc: int):
        pts = []
        for s in range(self.strings):
            for f in range(self.max_fret + 1):
                if (self.open_pc[s] + f) % 12 == pc:
                    pts.append((s, f))
        return pts

    def on_click(self, e):
        if not (self.open_x0 <= e.x <= self.x1 and self.y0 <= e.y <= self.y1):
            return

        s = min(range(self.strings), key=lambda i: abs(self.string_y[i] - e.y))
        fret = self.x_to_fret(e.x)

        pc = (self.open_pc[s] + fret) % 12

        group = self.points_for_pc(pc)
        if any(p in self.active_points for p in group):
            for p in group:
                self.active_points.discard(p)
        else:
            for p in group:
                self.active_points.add(p)

        semis = (pc - self.tonic_pc) % 12
        self.click_info.config(
            text=f"선택: {s+1}번줄 {'오픈' if fret==0 else str(fret)+'프렛'}, {self.pc_to_note_text(pc)}, {self.tension_label(semis)}"
        )
        self.draw()


def main():
    root = tk.Tk()
    Fretboard12Proto1(root)
    root.mainloop()


if __name__ == "__main__":
    main()
