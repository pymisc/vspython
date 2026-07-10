from PIL import Image, ImageDraw, ImageFont

# Define image boundaries and layout
width, height = 800, 500
bg_color = (23, 28, 36)      # Modern dark slate background
text_color = (255, 255, 255)  # White text
line_color = (70, 80, 95)     # Muted grey for connections
packet_color = (0, 255, 128)  # Bright neon green for the active request

# Define coordinates for infrastructure milestones
stages = [
    {"name": "User Browser", "pos": (80, 250)},
    {"name": "Route53 / DNS", "pos": (240, 100)},
    {"name": "AWS ALB / Ingress", "pos": (400, 250)},
    {"name": "K8s Pods", "pos": (580, 250)},
    {"name": "EFS / EBS Storage", "pos": (720, 250)}
]

# Total path nodes the packet will visit in order
path_nodes = [0, 1, 0, 2, 3, 4] 

frames = []
steps_per_leg = 15  # Smoothness of movement between nodes

# Linear interpolation helper to find packet positions
def interpolate(p1, p2, t):
    return (int(p1[0] + (p2[0] - p1[0]) * t), int(p1[1] + (p2[1] - p1[1]) * t))

# Generate the sequence of frames
for leg in range(len(path_nodes) - 1):
    start_node = stages[path_nodes[leg]]
    end_node = stages[path_nodes[leg+1]]
    
    for step in range(steps_per_leg):
        # Create a fresh canvas for this frame
        frame = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(frame)
        
        # 1. Draw architectural connection layout lines
        draw.line([stages[0]["pos"], stages[1]["pos"]], fill=line_color, width=2) # User to DNS
        draw.line([stages[0]["pos"], stages[2]["pos"]], fill=line_color, width=2) # User to ALB
        draw.line([stages[2]["pos"], stages[3]["pos"]], fill=line_color, width=2) # ALB to Pods
        draw.line([stages[3]["pos"], stages[4]["pos"]], fill=line_color, width=2) # Pods to Storage
        
        # 2. Render the static component blocks
        for stage in stages:
            x, y = stage["pos"]
            # Draw node marker
            draw.rectangle([x - 50, y - 25, x + 50, y + 25], outline=(100, 120, 140), width=2, fill=(35, 43, 55))
            # Text label (fallback to default font if custom font isn't loaded)
            draw.text((x - 42, y - 8), stage["name"], fill=text_color)
            
        # 3. Calculate and render packet position
        t = step / steps_per_leg
        packet_pos = interpolate(start_node["pos"], end_node["pos"], t)
        draw.ellipse([packet_pos[0] - 8, packet_pos[1] - 8, packet_pos[0] + 8, packet_pos[1] + 8], fill=packet_color)
        
        frames.append(frame)

# Save the compiled network lifecycle animation
frames[0].save(
    "k8s_traffic_flow.gif",
    save_all=True,
    append_images=frames[1:],
    duration=40,  # Fast and fluid runtime
    loop=0
)

print("K8s networking flow blueprint saved as 'k8s_traffic_flow.gif'!")