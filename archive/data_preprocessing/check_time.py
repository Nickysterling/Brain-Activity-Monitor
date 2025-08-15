import pandas as pd

df = pd.read_csv("blink_15.csv")
first_time = df["timestamps"].iloc[0]
last_time = df["timestamps"].iloc[-1]
duration = last_time - first_time
print("Captured duration (seconds):", duration)
