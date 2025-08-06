import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.widgets import RangeSlider, Button
import matplotlib.ticker as ticker
from datetime import datetime
import tkinter as tk

# Load your CSV
df = pd.read_csv("your_data.csv")
x_col = df.columns[1]

# Detect x-axis type
is_time = pd.api.types.is_datetime64_any_dtype(df[x_col])
is_numeric = pd.api.types.is_numeric_dtype(df[x_col])
if is_time:
    df[x_col] = pd.to_datetime(df[x_col], errors='coerce')

y_columns = list(df.columns[1:])
colors = plt.cm.get_cmap('tab10', len(y_columns)).colors
default_col = y_columns[0]
default_color = colors[0]

# Screen size
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()
dpi = 100
fig = plt.figure(figsize=(screen_width / dpi, screen_height / dpi * 0.95), dpi=dpi)

# Layout
host_left = 0.08
max_host_width = 0.87
min_host_width = 0.5
spacing = 0.035
host_bottom = 0.18
host_top = 0.78
host_height = host_top - host_bottom

host_width = max_host_width
host = fig.add_axes([host_left, host_bottom, host_width, host_height])
host.set_xlabel(x_col, fontweight='bold')
if is_time:
    host.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=10))
    host.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b %H:%M'))
else:
    host.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))

plt.setp(host.xaxis.get_majorticklabels(), rotation=45, fontweight='bold')

host.set_ylabel(default_col, color=default_color, fontweight='bold')
host.tick_params(axis='y', colors=default_color)
host.spines["left"].set_color(default_color)
for label in host.get_yticklabels():
    label.set_fontweight('bold')
default_line, = host.plot(df[x_col], df[default_col], color=default_color)

active_axes = {default_col: (host, default_line)}
label_states = {}
right_axes_order = []

# Tags
tag_ax = fig.add_axes([host_left, 0.83, 0.84, 0.065])
tag_ax.axis("off")
tag_ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=tag_ax.transAxes, fill=False, edgecolor='gray'))
n_cols = 3
n_rows = (len(y_columns) + n_cols - 1) // n_cols
x_spacing = 1 / n_cols
y_spacing = 1 / (n_rows + 1)
label_texts = []

for idx, col in enumerate(y_columns):
    col_idx = idx % n_cols
    row_idx = idx // n_cols
    x = x_spacing * col_idx + 0.01
    y = 1 - (row_idx + 1) * y_spacing
    color = colors[idx]
    is_on = col == default_col
    label = f"[{'x' if is_on else ' '}] {col}"
    text_obj = tag_ax.text(x, y, label, color=color, fontsize=11,
                           ha='left', va='center', picker=True, fontweight='medium')
    label_texts.append((col, text_obj))
    label_states[col] = is_on

def update_layout():
    visible_right = [col for col in right_axes_order if col in active_axes and active_axes[col][1].get_visible()]
    num_active = len(visible_right)
    used_width = spacing * num_active
    new_width = max(min(max_host_width - used_width, max_host_width), min_host_width)
    host.set_position([host_left, host_bottom, new_width, host_height])
    for i, col in enumerate(visible_right):
        ax, _ = active_axes[col]
        ax.spines["right"].set_position(("axes", 1.0 + spacing * i))
        ax.get_yaxis().set_visible(True)
        ax.spines["right"].set_visible(True)

def on_pick(event):
    for col, text_obj in label_texts:
        if event.artist == text_obj:
            idx = y_columns.index(col)
            color = colors[idx]
            visible = label_states[col]
            if col == default_col:
                ax, line = active_axes[col]
                line.set_visible(not visible)
                ax.get_yaxis().set_visible(not visible)
                ax.spines["left"].set_visible(not visible)
            else:
                if col in active_axes:
                    ax, line = active_axes[col]
                    line.set_visible(not visible)
                    ax.get_yaxis().set_visible(not visible)
                    ax.spines["right"].set_visible(not visible)
                else:
                    ax = host.twinx()
                    ax.set_ylabel(col, color=color, fontweight='bold')
                    ax.tick_params(axis='y', colors=color)
                    ax.yaxis.label.set_color(color)
                    for label in ax.get_yticklabels():
                        label.set_fontweight('bold')
                    ax.spines["right"].set_color(color)
                    ax.get_yaxis().set_visible(True)
                    ax.spines["left"].set_visible(False)
                    ax.spines["top"].set_visible(False)
                    ax.spines["bottom"].set_visible(False)
                    line, = ax.plot(df[x_col], df[col], color=color)
                    active_axes[col] = (ax, line)
                    right_axes_order.append(col)
            label_states[col] = not visible
            text_obj.set_text(f"[{'x' if not visible else ' '}] {col}")
            update_layout()
            plt.draw()
            break

fig.canvas.mpl_connect('pick_event', on_pick)

fig.suptitle("Multi Y-Axis Plot with Zoom Slider, Reset Button, and Bold Axes",
             fontsize=15, fontweight='bold', y=0.93)

# Slider
slider_ax = fig.add_axes([0.15, 0.07, 0.68, 0.03])
if is_time:
    slider_min = mdates.date2num(df[x_col].min())
    slider_max = mdates.date2num(df[x_col].max())
    slider_valinit = (slider_min, slider_max)
elif is_numeric:
    slider_min = df[x_col].min()
    slider_max = df[x_col].max()
    slider_valinit = (slider_min, slider_max)
else:
    slider_min, slider_max, slider_valinit = 0, 1, (0, 1)

slider = RangeSlider(
    ax=slider_ax,
    label='Zoom X-Axis',
    valmin=slider_min,
    valmax=slider_max,
    valinit=slider_valinit,
    valstep=0.01,
    # valfmt=''
)
slider.label.set_fontweight('bold')  # Bold label

# Range label
range_ax = fig.add_axes([0.15, 0.03, 0.7, 0.03])
range_ax.axis("off")
range_text = range_ax.text(0, 0.5, "", ha="left", va="center", fontsize=11, fontweight='bold')

def update(val):
    min_val = slider.val[0]
    max_val = slider.val[1]
    if is_time:
        min_dt = mdates.num2date(min_val)
        max_dt = mdates.num2date(max_val)
        host.set_xlim(min_dt, max_dt)
        range_text.set_text(f"Selected Range: {min_dt.strftime('%d-%b %Y %H:%M')} → {max_dt.strftime('%d-%b %Y %H:%M')}")
    else:
        host.set_xlim(min_val, max_val)
        range_text.set_text(f"Selected Range: {min_val:.2f} → {max_val:.2f}")
    fig.canvas.draw_idle()

slider.on_changed(update)

# Reset button (left of slider)
button_ax = fig.add_axes([0.84, 0.07, 0.10, 0.035])
reset_button = Button(button_ax, 'Reset Zoom', hovercolor='lightgray')
def reset(event):
    slider.set_val(slider_valinit)
reset_button.on_clicked(reset)

plt.show()
