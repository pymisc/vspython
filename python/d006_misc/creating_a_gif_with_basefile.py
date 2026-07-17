from PIL import Image, ImageDraw
import os

# 1. Load your polished Gemini-generated base image
base_image_path = "k8s_base.png"

if not os.path.exists(base_image_path):
    print(f"Error: Please save the Gemini image as '{base_image_path}' in this folder first!")
    exit()

base_img = Image.open(base_image_path).convert("RGB")
width, height = base_img.size

# 2. Coordinates of the icons on the generated image
stages = [
    (int(width * 0.10), int(height * 0.50)),  # User Request
    (int(width * 0.30), int(height * 0.50)),  # DNS Resolution
    (int(width * 0.50), int(height * 0.50)),  # AWS ALB
    (int(width * 0.70), int(height * 0.50)),  # K8s Pods
    (int(width * 0.90), int(height * 0.50))   # Underlying Storage
]

# The logical journey path sequence
path_nodes = [0, 1, 0, 2, 3, 4] 

frames = []

# --- SPEED CONFIGURATION ---
# Increased from 20 to 40 to double the frame count per leg for 50% slower, ultra-smooth motion
steps_per_leg = 40 
frame_duration = 45  # Milliseconds per frame for natural pacing
# ----------------------------

packet_color = (0, 200, 115) # Polished emerald green for the data packet

def interpolate(p1, p2, t):
    return (int(p1[0] + (p2[0] - p1[0]) * t), int(p1[1] + (p2[1] - p1[1]) * t))

print("Compiling half-speed animation over the polished background...")

# 3. Animate the dot over the background
for leg in range(len(path_nodes) - 1):
    start_node = stages[path_nodes[leg]]
    end_node = stages[path_nodes[leg+1]]
    
    for step in range(steps_per_leg):
        # Create a fresh copy of the base image for this frame
        frame = base_img.copy()
        draw = ImageDraw.Draw(frame)
        
        # Calculate packet position along the leg
        t = step / steps_per_leg
        packet_pos = interpolate(start_node, end_node, t)
        
        # Draw a glowing, polished data packet dot
        # Inner core
        draw.ellipse([packet_pos[0] - 10, packet_pos[1] - 10, packet_pos[0] + 10, packet_pos[1] + 10], fill=packet_color)
        # Outer soft ring
        draw.ellipse([packet_pos[0] - 14, packet_pos[1] - 14, packet_pos[0] + 14, packet_pos[1] + 14], outline=packet_color, width=2)
        
        frames.append(frame)

# 4. Export the final half-speed GIF
output_filename = "polished_k8s_traffic_slow.gif"
frames[0].save(
    output_filename,
    save_all=True,
    append_images=frames[1:],
    duration=frame_duration,
    loop=0
)

print(f"Success! Your half-speed animation is saved as '{output_filename}'.")