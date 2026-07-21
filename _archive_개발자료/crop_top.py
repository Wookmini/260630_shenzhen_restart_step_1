from PIL import Image

src = r"_발표자료\V1\img_workflow.png"
dst = r"_발표자료\V2\images\workflow_cropped_16x9.png"

try:
    img = Image.open(src).convert("RGBA")
    
    # We want a 16:9 crop of the top portion
    target_ratio = 16 / 9.0
    
    # Use full width
    crop_w = img.width
    crop_h = int(crop_w / target_ratio)
    
    # If the image is somehow wider than 16:9 (rare), handle it
    if crop_h > img.height:
        crop_h = img.height
        crop_w = int(crop_h * target_ratio)
        
    # Crop from top + offset (to push elements higher up in the frame)
    offset = 120  # Shift crop window down by 120 pixels
    left = (img.width - crop_w) // 2
    top = offset
    right = left + crop_w
    bottom = top + crop_h
    
    # Ensure bottom doesn't exceed image height
    if bottom > img.height:
        diff = bottom - img.height
        bottom = img.height
        top = max(0, top - diff)
    
    cropped = img.crop((left, top, right, bottom))
    cropped.save(dst)
    
    print(f"Successfully cropped to {crop_w}x{crop_h} (16:9) focusing on the top with {offset}px offset.")
except Exception as e:
    print(f"Error: {e}")
