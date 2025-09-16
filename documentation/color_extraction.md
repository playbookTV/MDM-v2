# Enhanced Color Extraction Documentation

## Overview

The enhanced color extraction system provides sophisticated color palette analysis for interior design images using K-means clustering and perceptual color space conversions. This replaces the simple pixel counting approach with a more accurate clustering-based algorithm that identifies truly dominant colors.

## Features

### 1. K-means Clustering Algorithm
- **Primary Method**: Uses scikit-learn's K-means clustering to identify dominant color clusters
- **Intelligent Sampling**: Samples a fraction of pixels for faster processing on large images
- **Deterministic Output**: Supports seed parameter for reproducible results

### 2. Perceptual Color Analysis
- **LAB Color Space**: Converts RGB to LAB for perceptual color difference calculations
- **Color Diversity Metrics**: Calculates palette diversity score (0-1 scale)
- **Semantic Color Names**: Maps colors to human-readable names (red, blue, teal, etc.)

### 3. Graceful Fallbacks
- **Multiple Methods**: Falls back to PIL quantization or pixel counting if sklearn unavailable
- **Error Handling**: Returns sensible defaults on failure
- **Method Reporting**: Reports which extraction method was used

## API Reference

### Main Function: `extract_color_palette_advanced`

```python
def extract_color_palette_advanced(
    image: PIL.Image.Image,
    n_colors: int = 5,
    sample_fraction: float = 0.1,
    seed: Optional[int] = 42
) -> Dict[str, Any]
```

#### Parameters

- **image** (`PIL.Image.Image`): Input image in any PIL-compatible format
- **n_colors** (`int`, default=5): Number of dominant colors to extract (1-10)
- **sample_fraction** (`float`, default=0.1): Fraction of pixels to sample (0.001-1.0)
- **seed** (`Optional[int]`, default=42): Random seed for reproducible K-means clustering

#### Returns

Dictionary containing:

```python
{
    "dominant_colors": [
        {
            "rgb": [r, g, b],           # RGB values (0-255)
            "hex": "#rrggbb",           # Hex color code
            "frequency": 0.234,         # Proportion of image (0-1)
            "lab": [L, a, b],          # LAB color space values
            "name": "teal"             # Semantic color name (if matched)
        },
        # ... more colors
    ],
    "palette_size": 5,                 # Number of colors extracted
    "color_diversity": 0.67,           # Diversity score (0-1)
    "extraction_method": "kmeans"      # Method used
}
```

### Backwards Compatible Function

```python
def extract_color_palette(image: PIL.Image.Image) -> Dict[str, Any]
```

Maintains compatibility with existing code, using default parameters.

## Color Extraction Methods

### 1. K-means (Primary)
- **When Used**: When scikit-learn is available
- **Advantages**: Most accurate, handles gradients well
- **Performance**: O(n_pixels * sample_fraction * n_colors * iterations)

### 2. PIL Quantization (Fallback)
- **When Used**: When sklearn unavailable
- **Method**: MEDIANCUT algorithm
- **Performance**: Faster but less accurate

### 3. Pixel Counting (Ultimate Fallback)
- **When Used**: When other methods fail
- **Method**: Simple frequency counting
- **Limitations**: May miss important but less frequent colors

## Integration with RunPod

The enhanced color extraction is integrated into the RunPod handler:

```python
# In handler_fixed.py
def extract_color_palette(image: Image.Image) -> dict:
    """Extract dominant colors using enhanced algorithm"""
    try:
        from app.services.color_extraction import extract_color_palette_advanced
        result = extract_color_palette_advanced(
            image, 
            n_colors=5, 
            sample_fraction=0.1,
            seed=42  # For reproducibility
        )
        return result
    except ImportError:
        # Falls back to simple method
        ...
```

## Database Storage

Color palettes are stored in the Supabase `scenes.palette` field as JSONB:

```sql
palette JSONB -- Format: [{"hex":"#aabbcc","p":0.23},...]
```

The worker transforms the extracted colors to match this schema:

```python
# Worker saves simplified format for database
palette_for_db = [
    {"hex": color["hex"], "p": color["frequency"]} 
    for color in result["dominant_colors"]
]
```

## Usage Examples

### Basic Usage

```python
from PIL import Image
from app.services.color_extraction import extract_color_palette_advanced

# Load image
image = Image.open("living_room.jpg").convert("RGB")

# Extract colors with defaults
palette = extract_color_palette_advanced(image)

# Print dominant color
print(f"Dominant color: {palette['dominant_colors'][0]['hex']}")
print(f"Coverage: {palette['dominant_colors'][0]['frequency']*100:.1f}%")
```

### Custom Parameters

```python
# Extract more colors with higher sampling
palette = extract_color_palette_advanced(
    image,
    n_colors=8,           # Get 8 colors
    sample_fraction=0.5,  # Sample 50% of pixels
    seed=123             # Different seed for variation
)

# Check extraction method
print(f"Method used: {palette['extraction_method']}")
```

### Analyzing Color Diversity

```python
# Get palette with diversity metrics
palette = extract_color_palette_advanced(image)

if palette['color_diversity'] > 0.7:
    print("High color diversity - vibrant, varied palette")
elif palette['color_diversity'] > 0.4:
    print("Moderate diversity - balanced color scheme")
else:
    print("Low diversity - monochromatic or limited palette")
```

### Working with Color Names

```python
palette = extract_color_palette_advanced(image)

for color in palette['dominant_colors']:
    if color.get('name'):
        print(f"{color['name']}: {color['hex']} ({color['frequency']*100:.1f}%)")
```

### Perceptual Color Analysis

```python
# Access LAB values for perceptual analysis
palette = extract_color_palette_advanced(image)

for i, color in enumerate(palette['dominant_colors']):
    lab = color['lab']
    print(f"Color {i+1}:")
    print(f"  Lightness: {lab[0]:.1f}")  # 0-100
    print(f"  Red-Green: {lab[1]:.1f}")  # Negative=green, Positive=red
    print(f"  Blue-Yellow: {lab[2]:.1f}") # Negative=blue, Positive=yellow
```

## Performance Considerations

### Image Size Optimization

- Images > 10,000 pixels: Automatic sampling applied
- Images < 10,000 pixels: All pixels used
- Large images (>1MP): Performance logged automatically

### Sampling Strategy

```python
# Adjust sampling based on image size
if image.size[0] * image.size[1] > 1_000_000:
    sample_fraction = 0.05  # 5% for large images
else:
    sample_fraction = 0.2   # 20% for medium images
```

### Memory Usage

- Maximum 10 colors to prevent memory issues
- Resizing applied during sampling phase
- Original image never modified

## Testing

Comprehensive test suite covers:

1. **Single color images**: Verify frequency = 1.0
2. **Deterministic output**: Same seed = same results
3. **Grayscale conversion**: Proper RGB palette generation
4. **Edge cases**: Empty images, tiny samples
5. **Color naming**: Semantic label accuracy
6. **LAB conversion**: Perceptual color space accuracy
7. **Diversity metrics**: Palette variety scoring

Run tests with:

```bash
cd backend
source venv/bin/activate
python -m pytest tests/test_color_extraction.py -v
```

## Frontend Display

The React frontend displays color palettes as interactive swatches:

```typescript
// TypeScript interface
interface ColorPalette {
  hex: string
  p: number  // Percentage/proportion
}

// React component renders swatches with tooltips
{scene.palette?.map((color, index) => (
  <Tooltip key={index}>
    <TooltipTrigger>
      <div
        className="h-10 rounded-md shadow-sm"
        style={{ backgroundColor: color.hex }}
      />
    </TooltipTrigger>
    <TooltipContent>
      <div>{color.hex}</div>
      <div>{(color.p * 100).toFixed(1)}% coverage</div>
    </TooltipContent>
  </Tooltip>
))}
```

## Migration from Old System

### Before (Simple Pixel Counting)
```python
# Old method - just counts pixels
color_counts = Counter(pixels)
dominant_colors = color_counts.most_common(5)
```

### After (K-means Clustering)
```python
# New method - intelligent clustering
kmeans = KMeans(n_clusters=5, random_state=42)
kmeans.fit(pixels)
dominant_colors = kmeans.cluster_centers_
```

### Benefits
- ✅ More accurate color identification
- ✅ Handles gradients and subtle variations
- ✅ Perceptual color information (LAB)
- ✅ Human-readable color names
- ✅ Diversity metrics
- ✅ Reproducible results

## Troubleshooting

### Issue: Colors Don't Match Visual Perception

**Solution**: Increase sample_fraction for better accuracy:
```python
palette = extract_color_palette_advanced(image, sample_fraction=0.5)
```

### Issue: Non-Deterministic Results

**Solution**: Always provide a seed:
```python
palette = extract_color_palette_advanced(image, seed=42)
```

### Issue: Missing scikit-learn

**Solution**: Install sklearn or system will use fallback:
```bash
pip install scikit-learn
```

### Issue: Too Many Similar Colors

**Solution**: Reduce n_colors to get more distinct clusters:
```python
palette = extract_color_palette_advanced(image, n_colors=3)
```

## Future Enhancements

Potential improvements (not yet implemented):

1. **Color Harmony Analysis**: Identify complementary, analogous, triadic schemes
2. **Seasonal Palettes**: Map colors to seasons (spring, summer, fall, winter)
3. **Brand Color Matching**: Compare to design system color libraries
4. **Accessibility Scoring**: WCAG contrast ratio analysis
5. **GPU Acceleration**: CUDA-accelerated clustering for batch processing
6. **Advanced Clustering**: DBSCAN or hierarchical clustering options

## References

- [K-means Clustering](https://scikit-learn.org/stable/modules/clustering.html#k-means)
- [CIE LAB Color Space](https://en.wikipedia.org/wiki/CIELAB_color_space)
- [Color Quantization](https://en.wikipedia.org/wiki/Color_quantization)
- [PIL Image Quantization](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize)