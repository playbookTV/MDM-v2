## TASK-005
---
STATUS: DONE

Implement extract_color_palette_advanced with the following contract:
- Input: 
  - image: PIL.Image.Image (RGB mode)
  - n_colors: int = 5 (number of dominant colors to extract)
  - sample_fraction: float = 0.1 (fraction of pixels to sample for speed)
  - seed: Optional[int] = 42 (for reproducible k-means)
- Output: Dict[str, Any]
  ```python
  {
    "dominant_colors": List[{
      "rgb": List[int],  # [r, g, b] values 0-255
      "hex": str,        # "#rrggbb" format
      "frequency": float,  # 0.0-1.0 proportion
      "lab": List[float],  # [L, a, b] perceptual values
      "name": Optional[str]  # semantic color name if available
    }],
    "palette_size": int,
    "color_diversity": float,  # 0.0-1.0 measure of palette variety
    "extraction_method": str  # "kmeans" or fallback method used
  }
  ```
- Preconditions:
  - image.mode == "RGB" or convertible to RGB
  - 1 <= n_colors <= 10
  - 0.001 <= sample_fraction <= 1.0
- Postconditions:
  - len(dominant_colors) <= n_colors
  - sum(frequencies) ≈ 1.0 (within 0.01 tolerance)
  - All RGB values in [0, 255]
  - Colors sorted by frequency descending
- Invariants:
  - Input image not mutated
  - Deterministic output when seed provided
- Error handling:
  - Invalid/corrupt image → return fallback with single gray color
  - K-means convergence failure → fallback to quantization method
  - Empty image → return empty palette
- Performance: O(n_pixels * sample_fraction * n_colors * iterations)
- Thread safety: Function is pure/stateless

Generate the implementation using K-means clustering with sklearn, with fallback to PIL quantization.
Include RGB to LAB conversion for perceptual color difference.
Add semantic color naming for common colors.
Include docstring with examples.
Add type hints for all parameters and return values.

Environment assumptions:
- Runtime: Python 3.11
- Frameworks/libs: PIL, numpy, scikit-learn, scipy (for LAB conversion)
- Integration points: RunPod handler (replace existing extract_color_palette)
- Determinism: sklearn KMeans with fixed random_state when seed provided

Test cases that MUST pass:
1. Single-color image returns one dominant color with frequency=1.0
2. Known test image returns consistent palette when seed=42
3. Grayscale image converts properly to RGB palette
4. sample_fraction=0.001 still produces valid output
5. n_colors > unique_colors returns only unique colors

File changes:
- Create: `backend/app/services/color_extraction.py`
- Modify: `backend/handler_fixed.py` (update extract_color_palette function)
- Create tests: `backend/tests/test_color_extraction.py`
- Avoid changes to: database schema, API contracts

Observability:
- Log extraction method used (kmeans vs fallback)
- Log timing for images > 1000x1000
- Log when sample_fraction adjusted due to small image

Safeguards:
- Enforce YAGNI: no color harmony analysis or palette generation
- No external color API calls
- Maximum 10 colors to prevent memory issues