from PIL import Image

# --- Load frames in chronological order ---
frames = [
    Image.open("figures/covid_2021_06_29.png"),
    Image.open("figures/covid_2022_07_27.png"),
    Image.open("figures/covid_2023_02_19.png")
]

# --- Resize frames for GitHub optimization (1280x720) ---
frames = [img.resize((1280, 720)) for img in frames]

# --- Add pause on final frame (policy-friendly ending) ---
frames.append(frames[-1])

# --- Save animated GIF ---
frames[0].save(
    "figures/covid_temporal_progression.gif",
    format="GIF",
    append_images=frames[1:],
    save_all=True,
    duration=2000,  # 2 seconds per frame
    loop=0
)

print("GIF successfully created: figures/covid_temporal_progression.gif")
