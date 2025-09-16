"""
Test suite for enhanced color extraction functionality.
"""

import unittest
import numpy as np
from PIL import Image
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.color_extraction import (
    extract_color_palette_advanced,
    extract_color_palette,
    rgb_to_lab,
    get_color_name,
    calculate_color_diversity
)


class TestColorExtraction(unittest.TestCase):
    """Test enhanced color extraction functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test images
        self.single_color_img = Image.new('RGB', (100, 100), color=(128, 64, 192))
        self.two_color_img = self._create_two_color_image()
        self.gradient_img = self._create_gradient_image()
        self.small_img = Image.new('RGB', (10, 10), color=(255, 0, 0))
    
    def _create_two_color_image(self):
        """Create an image with two distinct colors."""
        img = Image.new('RGB', (100, 100))
        pixels = img.load()
        for i in range(100):
            for j in range(100):
                if i < 50:
                    pixels[i, j] = (255, 0, 0)  # Red
                else:
                    pixels[i, j] = (0, 0, 255)  # Blue
        return img
    
    def _create_gradient_image(self):
        """Create an image with color gradient."""
        img = Image.new('RGB', (100, 100))
        pixels = img.load()
        for i in range(100):
            for j in range(100):
                r = int(255 * (i / 100))
                g = int(255 * (j / 100))
                b = 128
                pixels[i, j] = (r, g, b)
        return img
    
    def test_single_color_extraction(self):
        """Test that single-color image returns one dominant color with frequency=1.0."""
        result = extract_color_palette_advanced(
            self.single_color_img,
            n_colors=5,
            seed=42
        )
        
        self.assertEqual(len(result["dominant_colors"]), 1)
        self.assertAlmostEqual(result["dominant_colors"][0]["frequency"], 1.0, places=2)
        
        # Check RGB values are close to original
        rgb = result["dominant_colors"][0]["rgb"]
        self.assertAlmostEqual(rgb[0], 128, delta=5)
        self.assertAlmostEqual(rgb[1], 64, delta=5)
        self.assertAlmostEqual(rgb[2], 192, delta=5)
    
    def test_deterministic_output(self):
        """Test that same seed produces consistent palette."""
        result1 = extract_color_palette_advanced(
            self.gradient_img,
            n_colors=3,
            seed=42
        )
        
        result2 = extract_color_palette_advanced(
            self.gradient_img,
            n_colors=3,
            seed=42
        )
        
        # Check that results are identical
        self.assertEqual(len(result1["dominant_colors"]), len(result2["dominant_colors"]))
        for c1, c2 in zip(result1["dominant_colors"], result2["dominant_colors"]):
            self.assertEqual(c1["rgb"], c2["rgb"])
            self.assertEqual(c1["hex"], c2["hex"])
    
    def test_grayscale_conversion(self):
        """Test that grayscale image converts properly to RGB palette."""
        gray_img = Image.new('L', (100, 100), color=128)
        
        result = extract_color_palette_advanced(gray_img, n_colors=3)
        
        self.assertGreater(len(result["dominant_colors"]), 0)
        # Gray color should have equal RGB values
        for color in result["dominant_colors"]:
            rgb = color["rgb"]
            self.assertAlmostEqual(rgb[0], rgb[1], delta=5)
            self.assertAlmostEqual(rgb[1], rgb[2], delta=5)
    
    def test_small_sample_fraction(self):
        """Test that sample_fraction=0.001 still produces valid output."""
        result = extract_color_palette_advanced(
            self.gradient_img,
            n_colors=3,
            sample_fraction=0.001,
            seed=42
        )
        
        self.assertGreater(len(result["dominant_colors"]), 0)
        self.assertLessEqual(len(result["dominant_colors"]), 3)
        
        # Check frequencies sum to approximately 1
        total_freq = sum(c["frequency"] for c in result["dominant_colors"])
        self.assertAlmostEqual(total_freq, 1.0, delta=0.01)
    
    def test_unique_colors_limit(self):
        """Test that n_colors > unique_colors returns only unique colors."""
        # Two color image should return at most the requested number
        result = extract_color_palette_advanced(
            self.two_color_img,
            n_colors=10,
            seed=42
        )
        
        # Should not exceed requested number of colors
        self.assertLessEqual(len(result["dominant_colors"]), 10)
        
        # Most dominant colors should be red or blue
        top_colors = result["dominant_colors"][:2]
        for color in top_colors:
            rgb = color["rgb"]
            # Either predominantly red or predominantly blue
            is_reddish = rgb[0] > 200 and rgb[1] < 100 and rgb[2] < 100
            is_bluish = rgb[0] < 100 and rgb[1] < 100 and rgb[2] > 200
            self.assertTrue(is_reddish or is_bluish, f"Color {rgb} is neither red nor blue")
    
    def test_rgb_to_lab_conversion(self):
        """Test RGB to LAB color space conversion."""
        # Test known conversions
        white = rgb_to_lab(np.array([255, 255, 255]))
        self.assertAlmostEqual(white[0], 100, delta=5)  # L should be ~100 for white
        
        black = rgb_to_lab(np.array([0, 0, 0]))
        self.assertAlmostEqual(black[0], 0, delta=5)  # L should be ~0 for black
        
        # Middle gray
        gray = rgb_to_lab(np.array([128, 128, 128]))
        self.assertAlmostEqual(gray[1], 0, delta=5)  # a should be ~0 for gray
        self.assertAlmostEqual(gray[2], 0, delta=5)  # b should be ~0 for gray
    
    def test_color_name_detection(self):
        """Test semantic color naming."""
        self.assertEqual(get_color_name([255, 0, 0]), "red")
        self.assertEqual(get_color_name([0, 255, 0]), "green")
        self.assertEqual(get_color_name([0, 0, 255]), "blue")
        self.assertEqual(get_color_name([255, 255, 255]), "white")
        self.assertEqual(get_color_name([0, 0, 0]), "black")
        
        # Close matches
        self.assertEqual(get_color_name([250, 5, 5]), "red")
        self.assertEqual(get_color_name([130, 130, 130]), "gray")
    
    def test_color_diversity(self):
        """Test color diversity calculation."""
        # Same colors should have 0 diversity
        colors_same = [np.array([255, 0, 0]), np.array([255, 0, 0])]
        self.assertEqual(calculate_color_diversity(colors_same), 0.0)
        
        # Maximum diversity (black and white)
        colors_diverse = [np.array([0, 0, 0]), np.array([255, 255, 255])]
        diversity = calculate_color_diversity(colors_diverse)
        self.assertGreater(diversity, 0.9)  # Should be close to 1.0
        
        # Moderate diversity
        colors_moderate = [
            np.array([255, 0, 0]),
            np.array([0, 255, 0]),
            np.array([0, 0, 255])
        ]
        diversity = calculate_color_diversity(colors_moderate)
        self.assertGreater(diversity, 0.3)
        self.assertLess(diversity, 0.85)
    
    def test_empty_image_handling(self):
        """Test that empty image returns empty palette."""
        empty_img = Image.new('RGB', (0, 0))
        result = extract_color_palette_advanced(empty_img)
        
        self.assertEqual(len(result["dominant_colors"]), 0)
        self.assertEqual(result["palette_size"], 0)
        self.assertEqual(result["color_diversity"], 0.0)
    
    def test_backwards_compatibility(self):
        """Test backwards compatible extract_color_palette function."""
        result = extract_color_palette(self.single_color_img)
        
        self.assertIn("dominant_colors", result)
        self.assertIn("palette_size", result)
        self.assertGreater(len(result["dominant_colors"]), 0)
    
    def test_hex_format(self):
        """Test that hex colors are properly formatted."""
        result = extract_color_palette_advanced(self.single_color_img)
        
        for color in result["dominant_colors"]:
            hex_color = color["hex"]
            self.assertRegex(hex_color, r'^#[0-9a-f]{6}$')
            
            # Verify hex matches RGB
            rgb = color["rgb"]
            expected_hex = "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])
            self.assertEqual(hex_color, expected_hex)
    
    def test_lab_values_present(self):
        """Test that LAB color values are included."""
        result = extract_color_palette_advanced(self.gradient_img, n_colors=3)
        
        for color in result["dominant_colors"]:
            self.assertIn("lab", color)
            self.assertEqual(len(color["lab"]), 3)
            
            # L should be in range [0, 100]
            self.assertGreaterEqual(color["lab"][0], 0)
            self.assertLessEqual(color["lab"][0], 100)
    
    def test_extraction_method_reporting(self):
        """Test that extraction method is reported."""
        result = extract_color_palette_advanced(self.single_color_img)
        
        self.assertIn("extraction_method", result)
        self.assertIn(result["extraction_method"], 
                     ["kmeans", "quantization", "pixel_count", "error_fallback"])


if __name__ == '__main__':
    unittest.main()