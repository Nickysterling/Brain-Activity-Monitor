import pandas as pd
import matplotlib.pyplot as plt

# Load your CSV file and adjust timestamps
df = pd.read_csv("D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/blinking/processed/data/blink_01.csv")
df["timestamps"] = df["timestamps"] - df["timestamps"].iloc[0]
df["annotation"] = "clean"

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df["timestamps"], df["TP10"], label="TP10")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Amplitude")
ax.set_title("Click on two spots to mark blink interval")
plt.legend()

clicks = []  # List to store click timestamps

def on_click(event):
    if event.inaxes != ax:
        return
    # Prevent additional clicks after two markers
    if len(clicks) >= 2:
        print("Two markers already set. No more markers can be added.")
        return
    ts_click = event.xdata
    clicks.append(ts_click)
    ax.axvline(ts_click, color="red", linestyle="--")
    plt.draw()
    print(f"Click recorded at {ts_click:.2f} seconds")
    
    # Once two clicks are recorded, annotate the interval
    if len(clicks) == 2:
        start_ts, end_ts = min(clicks), max(clicks)
        df.loc[(df["timestamps"] >= start_ts) & (df["timestamps"] <= end_ts), "annotation"] = "blink"
        print(f"Annotated blink from {start_ts:.2f} to {end_ts:.2f} seconds")
        # Draw a shaded region for visual feedback
        ax.axvspan(start_ts, end_ts, color="red", alpha=0.3)
        plt.draw()

fig.canvas.mpl_connect('button_press_event', on_click)
plt.show()

# Save the updated CSV file after closing the plot
df.to_csv("D:/Windows Folders/Desktop/Brain-Activity-Monitoring-BAM/project_directory/data/test/blink_01_annotated.csv", index=False)
