"""
Enhanced color palette extraction using K-means clustering and perceptual color analysis.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image
from collections import Counter

logger = logging.getLogger(__name__)

# Try to import sklearn for K-means clustering
try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    logger.warning("scikit-learn not available - using fallback color extraction")
    HAS_SKLEARN = False

# Try to import scipy for color space conversions
try:
    from scipy.spatial.distance import euclidean
    HAS_SCIPY = True
except ImportError:
    logger.warning("scipy not available - using basic color distance")
    HAS_SCIPY = False


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """
    Convert RGB to CIE LAB color space for perceptual color difference.
    
    LAB color space is designed to approximate human vision and provides
    more perceptually uniform color differences than RGB.
    
    Args:
        rgb: Array of RGB values [r, g, b] with range [0, 255]
        
    Returns:
        Array of LAB values [L, a, b] where:
        - L (lightness): 0 (black) to 100 (white)
        - a: negative (green) to positive (red)
        - b: negative (blue) to positive (yellow)
        
    Example:
        >>> white = rgb_to_lab(np.array([255, 255, 255]))
        >>> print(white)  # [100, 0, 0] approximately
    """
    # Normalize RGB to [0, 1]
    rgb = rgb / 255.0
    
    # Apply gamma correction (sRGB to linear RGB)
    mask = rgb > 0.04045
    rgb[mask] = ((rgb[mask] + 0.055) / 1.055) ** 2.4
    rgb[~mask] = rgb[~mask] / 12.92
    
    # Convert to XYZ using D65 illuminant
    matrix = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ])
    xyz = np.dot(rgb, matrix.T) * 100
    
    # Normalize by D65 illuminant
    xyz[0] = xyz[0] / 95.047
    xyz[1] = xyz[1] / 100.000
    xyz[2] = xyz[2] / 108.883
    
    # Apply function
    mask = xyz > 0.008856
    xyz[mask] = xyz[mask] ** (1/3)
    xyz[~mask] = (7.787 * xyz[~mask]) + (16/116)
    
    # Convert to LAB
    L = (116 * xyz[1]) - 16
    a = 500 * (xyz[0] - xyz[1])
    b = 200 * (xyz[1] - xyz[2])
    
    return np.array([L, a, b])


def get_color_name(rgb: List[int]) -> Optional[str]:
    """
    Get semantic color name for common colors using nearest neighbor matching.
    
    Compares input color against a database of known colors and returns
    the name of the closest match if within threshold distance.
    
    Args:
        rgb: [r, g, b] values with range 0-255
        
    Returns:
        Color name (e.g., "teal", "coral") or None if no close match
        
    Example:
        >>> get_color_name([255, 0, 0])  # "red"
        >>> get_color_name([0, 128, 128])  # "teal"
        >>> get_color_name([123, 45, 67])  # None (no close match)
    """
    # Basic color names with representative RGB values
    color_names = {
        "red": [255, 0, 0],
        "green": [0, 255, 0],
        "blue": [0, 0, 255],
        "yellow": [255, 255, 0],
        "cyan": [0, 255, 255],
        "magenta": [255, 0, 255],
        "white": [255, 255, 255],
        "black": [0, 0, 0],
        "gray": [128, 128, 128],
        "brown": [139, 69, 19],
        "orange": [255, 165, 0],
        "pink": [255, 192, 203],
        "purple": [128, 0, 128],
        "beige": [245, 245, 220],
        "navy": [0, 0, 128],
        "teal": [0, 128, 128],
        "olive": [128, 128, 0],
        "maroon": [128, 0, 0],
        "lime": [0, 255, 0],
        "aqua": [0, 255, 255],
        "silver": [192, 192, 192],
        "gold": [255, 215, 0],
        "indigo": [75, 0, 130],
        "violet": [238, 130, 238],
        "tan": [210, 180, 140],
        "coral": [255, 127, 80],
        "salmon": [250, 128, 114],
        "peach": [255, 218, 185],
        "mint": [152, 255, 152],
        "ivory": [255, 255, 240],
        "pearl": [250, 250, 250]
    }
    
    # Find closest color name using Euclidean distance
    min_distance = float('inf')
    closest_name = None
    
    for name, reference_rgb in color_names.items():
        distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb, reference_rgb)))
        if distance < min_distance and distance < 50:  # Threshold for close match
            min_distance = distance
            closest_name = name
    
    return closest_name


def calculate_color_diversity(colors: List[np.ndarray]) -> float:
    """
    Calculate diversity of color palette (0-1, higher is more diverse).
    
    Uses average Euclidean distance between all color pairs in RGB space.
    A score of 0 means all colors are identical, while 1 means maximum diversity.
    
    Args:
        colors: List of RGB color arrays [r, g, b] with values 0-255
        
    Returns:
        Diversity score between 0 and 1
        
    Example:
        >>> colors = [np.array([255, 0, 0]), np.array([0, 255, 0])]
        >>> diversity = calculate_color_diversity(colors)
        >>> print(f"Diversity: {diversity:.2f}")  # ~0.67
    """
    if len(colors) <= 1:
        return 0.0
    
    # Calculate pairwise distances between all color combinations
    distances = []
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            # Euclidean distance in RGB space
            dist = np.linalg.norm(colors[i] - colors[j])
            distances.append(dist)
    
    if not distances:
        return 0.0
    
    # Normalize by maximum possible distance
    # Max distance is between black [0,0,0] and white [255,255,255]
    # Which equals sqrt(3 * 255^2) ≈ 441.67
    max_possible = np.sqrt(3 * 255 * 255)
    avg_distance = np.mean(distances)
    diversity = min(1.0, avg_distance / max_possible)
    
    return diversity


def extract_color_palette_advanced(
    image: Image.Image,
    n_colors: int = 5,
    sample_fraction: float = 0.1,
    seed: Optional[int] = 42
) -> Dict[str, Any]:
    """
    Extract dominant color palette using K-means clustering with perceptual analysis.
    
    Args:
        image: PIL Image in RGB mode
        n_colors: Number of dominant colors to extract (1-10)
        sample_fraction: Fraction of pixels to sample for speed (0.001-1.0)
        seed: Random seed for reproducible K-means clustering
        
    Returns:
        Dictionary containing dominant colors with RGB, hex, LAB values and metadata
        
    Example:
        >>> img = Image.open("room.jpg").convert("RGB")
        >>> palette = extract_color_palette_advanced(img, n_colors=5, seed=42)
        >>> print(palette["dominant_colors"][0]["hex"])  # "#a4b5c6"
    """
    start_time = time.time()
    
    # Validate inputs
    n_colors = max(1, min(10, n_colors))
    sample_fraction = max(0.001, min(1.0, sample_fraction))
    
    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # Get image dimensions
    width, height = image.size
    total_pixels = width * height
    
    # Handle edge cases
    if total_pixels == 0:
        return {
            "dominant_colors": [],
            "palette_size": 0,
            "color_diversity": 0.0,
            "extraction_method": "empty"
        }
    
    # Adjust sample fraction for small images
    if total_pixels < 10000:
        sample_fraction = 1.0
        logger.debug(f"Small image ({width}x{height}), using all pixels")
    
    # Sample pixels for faster processing
    if sample_fraction < 1.0:
        # Resize for sampling
        sample_size = int(np.sqrt(total_pixels * sample_fraction))
        sample_size = max(50, sample_size)  # Minimum 50x50
        img_sampled = image.resize((sample_size, sample_size), Image.Resampling.LANCZOS)
    else:
        img_sampled = image
    
    # Convert to numpy array and reshape to list of pixels
    pixels = np.array(img_sampled)
    pixels_reshaped = pixels.reshape(-1, 3)
    
    # Determine extraction method based on available libraries
    extraction_method = "fallback"
    dominant_colors = []
    
    if HAS_SKLEARN:
        try:
            # Use K-means clustering
            extraction_method = "kmeans"
            
            # Determine actual number of clusters (can't exceed unique colors)
            unique_colors = len(np.unique(pixels_reshaped, axis=0))
            actual_n_colors = min(n_colors, unique_colors)
            
            if actual_n_colors == 1:
                # Single color image
                mean_color = pixels_reshaped.mean(axis=0)
                dominant_colors = [{
                    "rgb": mean_color.astype(int).tolist(),
                    "frequency": 1.0
                }]
            else:
                # Perform K-means clustering
                kmeans = KMeans(
                    n_clusters=actual_n_colors,
                    random_state=seed,
                    n_init=10,
                    max_iter=300
                )
                kmeans.fit(pixels_reshaped)
                
                # Get cluster centers and labels
                cluster_centers = kmeans.cluster_centers_
                labels = kmeans.labels_
                
                # Calculate frequency of each cluster
                label_counts = Counter(labels)
                total_samples = len(labels)
                
                # Create color entries
                for cluster_id, center in enumerate(cluster_centers):
                    frequency = label_counts[cluster_id] / total_samples
                    dominant_colors.append({
                        "rgb": center.astype(int).tolist(),
                        "frequency": frequency
                    })
            
            logger.debug(f"K-means extracted {len(dominant_colors)} colors")
            
        except Exception as e:
            logger.warning(f"K-means clustering failed: {e}, falling back to quantization")
            extraction_method = "fallback"
    
    # Fallback method using PIL quantization
    if extraction_method == "fallback" or not dominant_colors:
        try:
            extraction_method = "quantization"
            
            # Use PIL's quantize method
            img_quantized = img_sampled.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
            palette = img_quantized.getpalette()
            
            if palette:
                # Count pixels for each palette color
                img_indexed = np.array(img_quantized)
                color_counts = Counter(img_indexed.flatten())
                total_samples = img_indexed.size
                
                # Extract colors from palette
                dominant_colors = []
                for color_index, count in color_counts.most_common(n_colors):
                    if color_index * 3 + 2 < len(palette):
                        rgb = [
                            palette[color_index * 3],
                            palette[color_index * 3 + 1],
                            palette[color_index * 3 + 2]
                        ]
                        frequency = count / total_samples
                        dominant_colors.append({
                            "rgb": rgb,
                            "frequency": frequency
                        })
            else:
                # Ultimate fallback - simple pixel counting
                extraction_method = "pixel_count"
                pixel_list = [tuple(p) for p in pixels_reshaped]
                color_counts = Counter(pixel_list)
                total_samples = len(pixel_list)
                
                dominant_colors = []
                for color, count in color_counts.most_common(n_colors):
                    frequency = count / total_samples
                    dominant_colors.append({
                        "rgb": list(color),
                        "frequency": frequency
                    })
                    
        except Exception as e:
            logger.error(f"All color extraction methods failed: {e}")
            # Return gray as ultimate fallback
            dominant_colors = [{
                "rgb": [128, 128, 128],
                "frequency": 1.0
            }]
            extraction_method = "error_fallback"
    
    # Sort by frequency
    dominant_colors.sort(key=lambda x: x["frequency"], reverse=True)
    
    # Enhance color information
    enhanced_colors = []
    for color_data in dominant_colors:
        rgb = color_data["rgb"]
        
        # Ensure RGB values are valid
        rgb = [max(0, min(255, int(c))) for c in rgb]
        
        # Convert to hex
        hex_color = "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])
        
        # Convert to LAB if possible
        try:
            lab = rgb_to_lab(np.array(rgb, dtype=float))
            lab_values = lab.tolist()
        except Exception as e:
            logger.debug(f"LAB conversion failed: {e}")
            lab_values = [50.0, 0.0, 0.0]  # Default neutral gray in LAB
        
        # Get semantic color name
        color_name = get_color_name(rgb)
        
        enhanced_colors.append({
            "rgb": rgb,
            "hex": hex_color,
            "frequency": round(color_data["frequency"], 4),
            "lab": lab_values,
            "name": color_name
        })
    
    # Calculate color diversity
    if len(enhanced_colors) > 1:
        color_arrays = [np.array(c["rgb"]) for c in enhanced_colors]
        diversity = calculate_color_diversity(color_arrays)
    else:
        diversity = 0.0
    
    # Log performance for large images
    processing_time = time.time() - start_time
    if width > 1000 or height > 1000:
        logger.info(f"Color extraction for {width}x{height} image took {processing_time:.2f}s using {extraction_method}")
    
    return {
        "dominant_colors": enhanced_colors,
        "palette_size": len(enhanced_colors),
        "color_diversity": round(diversity, 4),
        "extraction_method": extraction_method
    }


# Compatibility function that matches the existing interface
def extract_color_palette(image: Image.Image) -> Dict[str, Any]:
    """
    Extract color palette using enhanced algorithm (backwards compatible).
    
    Args:
        image: PIL Image
        
    Returns:
        Dictionary with dominant_colors and palette_size
    """
    result = extract_color_palette_advanced(image, n_colors=5, sample_fraction=0.1, seed=None)
    
    # Convert to match existing format if needed
    return {
        "dominant_colors": result["dominant_colors"],
        "palette_size": result["palette_size"]
    }