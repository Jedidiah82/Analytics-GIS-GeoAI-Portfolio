import imageio
from PIL import Image

# Paths
gif_path = "figures/covid_temporal_progression.gif"
mp4_path = "figures/covid_temporal_progression.mp4"
preview_path = "figures/covid_temporal_preview.png"

# Load GIF frames
frames = imageio.mimread(gif_path)

# Resize frames for GitHub optimization
frames = [Image.fromarray(frame).resize((1280, 720)) for frame in frames]

# Save MP4
imageio.mimwrite(
    mp4_path,
    frames,
    fps=0.5,          # slow, policy-friendly pacing
    codec="libx264"
)

# Save preview image (final frame)
frames[-1].save(preview_path)

print("✅ MP4 and preview image created successfully.")
