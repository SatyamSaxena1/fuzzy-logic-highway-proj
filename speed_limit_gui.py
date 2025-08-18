"""speed_limit_gui.py

Simple Tkinter GUI that uses the pure-Python fuzzy controller to show
input sliders, membership functions, aggregated output membership and
defuzzified speed. Embeds matplotlib for plotting.

Run: python speed_limit_gui.py
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from speed_limit_pure import build_speed_mfs
from paper_rules import human_readable_rules

import logging

# lightweight console logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('speed_limit_gui')
logger.info('Starting speed_limit_gui (lightweight)')


def compute_aggregation_and_centroid(mfs, rc_val, td_val, gap_val):
    ui = mfs['uni_in']
    uo = mfs['uni_out']

    # membership degrees for inputs
    def interp(x, mf, val):
        return float(np.interp(val, x, mf))

    rc = np.array([interp(ui, mfs['poor'], rc_val), interp(ui, mfs['average'], rc_val), interp(ui, mfs['good'], rc_val)])
    td = np.array([interp(ui, mfs['poor'], td_val), interp(ui, mfs['average'], td_val), interp(ui, mfs['good'], td_val)])
    gap = np.array([interp(ui, mfs['poor'], gap_val), interp(ui, mfs['average'], gap_val), interp(ui, mfs['good'], gap_val)])

    labels = ['poor', 'average', 'good']

    # explicit mapping consistent with pure fallback
    mapping = {}
    for r in labels:
        for t in labels:
            for g in labels:
                if r == 'good' and g == 'good':
                    out = 'high'
                elif r == 'poor' and g == 'poor':
                    out = 'low'
                elif r == 'good' and g == 'average':
                    out = 'high'
                elif r == 'average' and g == 'good':
                    out = 'high'
                elif r == 'poor' and g == 'average':
                    out = 'low'
                else:
                    out = 'medium'
                mapping[(r, t, g)] = out

    # collect per-rule activations and clipped MFs
    rules = []
    for i, rlab in enumerate(labels):
        for j, tlab in enumerate(labels):
            for k, glab in enumerate(labels):
                r_val = rc[i]
                t_val = td[j]
                g_val = gap[k]
                activation = float(min(r_val, t_val, g_val))
                out_label = mapping[(rlab, tlab, glab)]
                # clipped mf for this rule
                if out_label == 'low':
                    clipped = np.fmin(activation, mfs['low'])
                elif out_label == 'medium':
                    clipped = np.fmin(activation, mfs['medium'])
                else:
                    clipped = np.fmin(activation, mfs['high'])
                rules.append(((rlab, tlab, glab, out_label), activation, clipped))

    # aggregate final mf
    agg = np.zeros_like(mfs['uni_out'], dtype=float)
    low_clips = []
    med_clips = []
    high_clips = []
    for (desc, act, clip) in rules:
        agg = np.fmax(agg, clip)
        if desc[3] == 'low':
            low_clips.append((desc, act, clip))
        elif desc[3] == 'medium':
            med_clips.append((desc, act, clip))
        else:
            high_clips.append((desc, act, clip))

    if agg.sum() == 0:
        centroid = 0.0
    else:
        centroid = float((agg * uo).sum() / agg.sum())

    # return centroid, aggregated mf, and per-rule list sorted by activation desc
    rules_sorted = sorted(rules, key=lambda r: r[1], reverse=True)
    return centroid, agg, rules_sorted


class SpeedLimitGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Fuzzy Speed Limit - GUI')
        self.geometry('900x700')

        self.mfs = build_speed_mfs()

        self.rc_var = tk.DoubleVar(value=5.0)
        self.td_var = tk.DoubleVar(value=5.0)
        self.gap_var = tk.DoubleVar(value=0.0)

        # left column controls
        controls = ttk.Frame(self)
        controls.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        self._add_slider(controls, 'Road conditions', self.rc_var, 0)
        self._add_slider(controls, 'Traffic density', self.td_var, 1)
        self._add_slider(controls, 'Gap in traffic', self.gap_var, 2)

        # top bar with actions and result
        btnframe = ttk.Frame(self)
        btnframe.pack(side=tk.TOP, fill=tk.X, padx=8)
        update_btn = ttk.Button(btnframe, text='Update', command=self.update_plot)
        update_btn.pack(side=tk.LEFT)
        save_btn = ttk.Button(btnframe, text='Save plot', command=self.save_plot)
        save_btn.pack(side=tk.LEFT, padx=6)
        save_example_btn = ttk.Button(btnframe, text='Save example', command=self.save_example)
        save_example_btn.pack(side=tk.LEFT, padx=6)

        # prominent result label (large font, colored)
        result_font = tkfont.Font(family='Helvetica', size=16, weight='bold')
        self.result_label = tk.Label(btnframe, text='Recommended: -- km/h', font=result_font)
        self.result_label.pack(side=tk.LEFT, padx=12)

        # copy button for the result
        copy_btn = ttk.Button(btnframe, text='Copy', command=lambda: self.clipboard_copy_result())
        copy_btn.pack(side=tk.LEFT)

        self.desc_var = tk.StringVar(value='')
        self.desc_label = ttk.Label(btnframe, textvariable=self.desc_var)
        self.desc_label.pack(side=tk.LEFT, padx=12)

        # menu to view inferred paper rules
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='View', menu=view_menu)
        view_menu.add_command(label='Show inferred 36 rules', command=self.show_rules)

        # Matplotlib figure in center
        self.fig, self.axes = plt.subplots(3, 1, figsize=(7, 8))
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        # create per-rule panel on the right
        self._create_rules_panel(self)

        self.last_centroid = None
        self.update_plot()

    def _add_slider(self, parent, text, var, column):
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=6)
        label = ttk.Label(frame, text=text)
        label.pack()
        s = ttk.Scale(frame, from_=0, to=10, orient=tk.HORIZONTAL, variable=var, command=lambda e: self.on_slide())
        s.pack()
        val = ttk.Label(frame, textvariable=var)
        val.pack()

    def on_slide(self):
        # throttle updates by after scheduling to avoid flood
        if hasattr(self, '_after_id'):
            self.after_cancel(self._after_id)
        self._after_id = self.after(120, self.update_plot)

    def update_plot(self):
        rc = float(self.rc_var.get())
        td = float(self.td_var.get())
        gap = float(self.gap_var.get())

        centroid, agg, rules_sorted = compute_aggregation_and_centroid(self.mfs, rc, td, gap)

        # clear axes
        for ax in self.axes:
            ax.clear()

        ui = self.mfs['uni_in']
        uo = self.mfs['uni_out']

        # Input MFs (show once)
        self.axes[0].plot(ui, self.mfs['poor'], 'r', label='poor')
        self.axes[0].plot(ui, self.mfs['average'], 'g', label='average')
        self.axes[0].plot(ui, self.mfs['good'], 'b', label='good')
        self.axes[0].set_title('Input MFs (0-10)')
        self.axes[0].legend()
        self.axes[0].set_xlim(0, 10)

        # Output MFs
        self.axes[1].plot(uo, self.mfs['low'], 'r', label='low')
        self.axes[1].plot(uo, self.mfs['medium'], 'g', label='medium')
        self.axes[1].plot(uo, self.mfs['high'], 'b', label='high')
        self.axes[1].set_title('Output MFs (speed 0-120)')
        self.axes[1].legend()
        self.axes[1].set_xlim(0, 120)

        # Defuzzified result: show aggregated clipped area and centroid
        self.axes[2].plot(uo, self.mfs['low'], color='r', alpha=0.2)
        self.axes[2].plot(uo, self.mfs['medium'], color='g', alpha=0.2)
        self.axes[2].plot(uo, self.mfs['high'], color='b', alpha=0.2)
        # overlay top rule clipped outputs (up to 6) with labels
        top_rules = rules_sorted[:6]
        colors = ['#8B0000', '#FF8C00', '#228B22', '#4169E1', '#800080', '#2F4F4F']
        for idx, (desc, act, clip) in enumerate(top_rules):
            self.axes[2].fill_between(uo, 0, clip, color=colors[idx % len(colors)], alpha=0.35, label=f'{desc[0]}/{desc[1]}/{desc[2]}->{desc[3]} ({act:.2f})')
        self.axes[2].plot(uo, agg, color='purple', linewidth=2, label='aggregated')
        self.axes[2].axvline(centroid, color='k', linestyle='--', label=f'defuzzified {centroid:.2f}')
        self.axes[2].set_title(f'Defuzzified result: {centroid:.2f} km/h')
        self.axes[2].set_xlim(0, 120)
        self.axes[2].legend(loc='upper left', fontsize='small')

    

    def clipboard_copy_result(self):
        try:
            if self.last_centroid is None:
                messagebox.showinfo('Copy', 'No result to copy yet')
                return
            txt = f'{self.last_centroid:.2f} km/h'
            self.clipboard_clear()
            self.clipboard_append(txt)
            messagebox.showinfo('Copied', f'Copied: {txt}')
        except Exception as e:
            messagebox.showerror('Error', f'Could not copy to clipboard: {e}')

    def save_plot(self):
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG files', '*.png')])
        if not path:
            return
        self.fig.savefig(path)

    def save_example(self):
        # save plot and a small JSON describing inputs
        import json, os
        os.makedirs('examples', exist_ok=True)
        rc = float(self.rc_var.get())
        td = float(self.td_var.get())
        gap = float(self.gap_var.get())
        centroid, agg, rules_sorted = compute_aggregation_and_centroid(self.mfs, rc, td, gap)
        base = f'examples/speed_rc{int(rc)}_td{int(td)}_gap{int(gap)}'
        png = base + '.png'
        meta = base + '.json'
        self.fig.savefig(png)
        with open(meta, 'w') as f:
            json.dump({'rc': rc, 'td': td, 'gap': gap, 'centroid': centroid}, f)
        messagebox.showinfo('Saved', f'Example saved: {png} and {meta}')

    def show_rules(self):
        rules = human_readable_rules()
        win = tk.Toplevel(self)
        win.title('Inferred paper rules (36)')
        txt = tk.Text(win, wrap='word', width=80, height=30)
        txt.pack(fill=tk.BOTH, expand=1)
        txt.insert('1.0', '\n'.join(rules))
        txt.config(state='disabled')

    # per-rule UI panel
    def _create_rules_panel(self, parent):
        # scrollable frame with top rules and progress bars
        container = ttk.Frame(parent)
        container.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        label = ttk.Label(container, text='Top rules (activation)')
        label.pack()
        canvas = tk.Canvas(container, width=320, height=300)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        self.rules_frame = ttk.Frame(canvas)
        self.rules_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self.rules_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _update_rules_panel(self, rules_sorted):
        # clear
        for w in getattr(self, '_rule_widgets', []):
            w.destroy()
        self._rule_widgets = []
        # show top 12 rules
        for idx, (desc, act, clip) in enumerate(rules_sorted[:12]):
            text = f'{desc[0]}/{desc[1]}/{desc[2]} -> {desc[3]} ({act:.2f})'
            lbl = ttk.Label(self.rules_frame, text=text)
            lbl.pack(anchor='w')
            pb = ttk.Progressbar(self.rules_frame, orient='horizontal', length=280, mode='determinate')
            pb['maximum'] = 1.0
            pb['value'] = act
            pb.pack()
            self._rule_widgets.extend([lbl, pb])

    def _update_description(self, rc, td, gap, centroid, rules_sorted):
        # simple, human-friendly description
        rc_label = 'Good' if rc >= 7 else ('Poor' if rc <= 3 else 'Average')
        td_label = 'High' if td >= 7 else ('Low' if td <= 3 else 'Medium')
        gap_label = 'Present' if gap >= 7 else ('Absent' if gap <= 3 else 'Some')
        top = rules_sorted[0][0]
        reason = f"Top rule: {top[0]}/{top[1]}/{top[2]} -> {top[3]}"
        desc = f'Road: {rc_label}. Traffic: {td_label}. Gap: {gap_label}. {reason}. Recommended {centroid:.1f} km/h.'
        self.desc_var.set(desc)


if __name__ == '__main__':
    try:
        logger.info('Creating GUI app instance')
        app = SpeedLimitGUI()
        logger.info('Entering mainloop')
        app.mainloop()
        logger.info('Mainloop exited normally')
    except Exception:
        logger.exception('Exception during app startup or mainloop')
        # ensure any buffered logs are written
        for h in logging.root.handlers:
            try:
                h.flush()
            except Exception:
                pass
        # re-raise so that PyInstaller bootloader may capture exit code if present
        raise
