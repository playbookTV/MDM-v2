"""
Bounding box validation and normalization utilities.

This module provides robust validation and conversion for bbox coordinates
to prevent negative width/height values in database storage.
"""

import logging
from typing import Union, Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


def detect_bbox_format(bbox_data: List[float]) -> str:
    """
    Detect if bbox is in [x1,y1,x2,y2] or [x,y,w,h] format.
    
    Args:
        bbox_data: List of 4 float values
        
    Returns:
        'xyxy' for [x1,y1,x2,y2] format, 'xywh' for [x,y,w,h] format
    """
    if len(bbox_data) != 4:
        return 'xywh'  # Default assumption
    
    x, y, w_or_x2, h_or_y2 = bbox_data
    
    # Strong indicators of [x1,y1,x2,y2] format:
    # 1. Third and fourth values are both positive and larger than first two
    # 2. Width/height calculation would be reasonable (> 0 and < 2000px typically)  
    # 3. Values suggest coordinates rather than dimensions
    if (w_or_x2 > x and h_or_y2 > y and 
        w_or_x2 - x > 0 and h_or_y2 - y > 0 and
        w_or_x2 - x < 2000 and h_or_y2 - y < 2000 and
        w_or_x2 > 50 and h_or_y2 > 50):  # Large enough to be coordinates
        return 'xyxy'
    
    # Strong indicators of [x,y,w,h] format:
    # 1. Third and fourth values are reasonable dimensions (typically 5-1000px)
    # 2. Values are small enough to be width/height rather than coordinates
    if (w_or_x2 > 0 and h_or_y2 > 0 and 
        w_or_x2 <= 2000 and h_or_y2 <= 2000):  
        return 'xywh'
    
    # If unclear, check for negative values (strong indicator of confusion)
    if w_or_x2 < 0 or h_or_y2 < 0:
        logger.warning(f"Negative values in bbox {bbox_data}, assuming coordinate confusion")
        return 'xyxy'  # Likely mixed up coordinates
    
    return 'xywh'  # Default


def convert_bbox_to_xywh(bbox_data: List[float], format_hint: Optional[str] = None) -> Tuple[float, float, float, float]:
    """
    Convert bbox to normalized [x, y, width, height] format.
    
    Args:
        bbox_data: List of 4 coordinates
        format_hint: Optional format hint ('xyxy' or 'xywh')
        
    Returns:
        Tuple of (x, y, width, height) with positive dimensions
        
    Raises:
        ValueError: If bbox cannot be converted to valid format
    """
    if len(bbox_data) != 4:
        raise ValueError(f"Invalid bbox length: {len(bbox_data)}, expected 4")
    
    # Detect format if not provided
    if format_hint is None:
        format_hint = detect_bbox_format(bbox_data)
    
    if format_hint == 'xyxy':
        # Convert [x1,y1,x2,y2] to [x,y,w,h]
        x1, y1, x2, y2 = bbox_data
        
        # Ensure proper ordering
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
            
        x, y = x1, y1
        width = x2 - x1
        height = y2 - y1
        
    else:  # format_hint == 'xywh'
        x, y, width, height = bbox_data
    
    # Ensure all values are positive
    x = max(0, x)
    y = max(0, y)
    width = abs(width)
    height = abs(height)
    
    # Validate final dimensions
    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid bbox dimensions: width={width}, height={height}")
    
    return x, y, width, height


def clamp_bbox_to_image(x: float, y: float, width: float, height: float, 
                       image_width: int, image_height: int) -> Tuple[float, float, float, float]:
    """
    Clamp bbox coordinates to image boundaries.
    
    Args:
        x, y, width, height: Bbox coordinates
        image_width, image_height: Image dimensions
        
    Returns:
        Clamped (x, y, width, height) tuple
    """
    # Clamp position to image bounds
    x = max(0, min(x, image_width - 1))
    y = max(0, min(y, image_height - 1))
    
    # Adjust width/height to not exceed image bounds
    width = min(width, image_width - x)
    height = min(height, image_height - y)
    
    # Ensure minimum size
    width = max(1, width)
    height = max(1, height)
    
    return x, y, width, height


def validate_and_normalize_bbox(
    bbox_data: Union[List, Dict, Any], 
    object_index: int = 0,
    image_width: Optional[int] = None,
    image_height: Optional[int] = None,
    min_area: int = 1,
    format_hint: Optional[str] = None
) -> Dict[str, int]:
    """
    Comprehensive bbox validation and normalization.
    
    Args:
        bbox_data: Bbox in various formats (list, dict)
        object_index: Index for logging
        image_width, image_height: Optional image dimensions for clamping
        min_area: Minimum required area in pixels
        
    Returns:
        Normalized bbox dict: {'x': int, 'y': int, 'width': int, 'height': int}
        
    Raises:
        ValueError: If bbox is invalid and cannot be fixed
    """
    logger.debug(f"Validating bbox for object {object_index}: {bbox_data}")
    
    try:
        # Handle different input formats
        if isinstance(bbox_data, list):
            if len(bbox_data) != 4:
                raise ValueError(f"Invalid bbox list length: {len(bbox_data)}")
            
            # Convert to float for processing
            bbox_list = [float(x) for x in bbox_data]
            x, y, width, height = convert_bbox_to_xywh(bbox_list, format_hint=format_hint)
            
        elif isinstance(bbox_data, dict):
            # Handle dict format - ONLY accept x,y,width,height format
            if 'x' in bbox_data and 'y' in bbox_data:
                x = float(bbox_data.get('x', 0))
                y = float(bbox_data.get('y', 0))
                width = float(bbox_data.get('width', bbox_data.get('w', 0)))
                height = float(bbox_data.get('height', bbox_data.get('h', 0)))
            elif 'x1' in bbox_data or 'x2' in bbox_data or 'y1' in bbox_data or 'y2' in bbox_data:
                raise ValueError(f"x1,y1,x2,y2 format is not supported. Use x,y,width,height format instead: {bbox_data}")
            else:
                raise ValueError(f"Invalid bbox dict format. Expected x,y,width,height: {bbox_data}")
                
        else:
            raise ValueError(f"Unsupported bbox format: {type(bbox_data)}")
        
        # Apply image bounds clamping if provided
        if image_width is not None and image_height is not None:
            x, y, width, height = clamp_bbox_to_image(
                x, y, width, height, image_width, image_height
            )
        
        # Final validation
        area = width * height
        if area < min_area:
            raise ValueError(f"Bbox area too small: {area} < {min_area}")
        
        # Convert to integers for storage
        result = {
            'x': int(round(x)),
            'y': int(round(y)),
            'width': int(round(width)),
            'height': int(round(height))
        }
        
        logger.debug(f"Normalized bbox for object {object_index}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Bbox validation failed for object {object_index}: {e}")
        logger.error(f"Input bbox data: {bbox_data}")
        raise ValueError(f"Cannot validate bbox for object {object_index}: {e}")


def is_valid_bbox(bbox: Dict[str, Any]) -> bool:
    """
    Check if bbox dict has valid positive dimensions.
    
    Args:
        bbox: Dict with 'x', 'y', 'width', 'height' keys
        
    Returns:
        True if bbox is valid, False otherwise
    """
    try:
        x = bbox.get('x', 0)
        y = bbox.get('y', 0)
        width = bbox.get('width', 0)
        height = bbox.get('height', 0)
        
        return (isinstance(x, (int, float)) and x >= 0 and
                isinstance(y, (int, float)) and y >= 0 and
                isinstance(width, (int, float)) and width > 0 and
                isinstance(height, (int, float)) and height > 0)
    except Exception:
        return False


def calculate_bbox_area(bbox: Dict[str, Any]) -> float:
    """Calculate the area of a bbox."""
    return bbox.get('width', 0) * bbox.get('height', 0)


def calculate_bbox_iou(bbox1: Dict[str, Any], bbox2: Dict[str, Any]) -> float:
    """
    Calculate Intersection over Union (IoU) of two bboxes.
    
    Args:
        bbox1, bbox2: Bbox dicts with 'x', 'y', 'width', 'height'
        
    Returns:
        IoU score between 0 and 1
    """
    if not (is_valid_bbox(bbox1) and is_valid_bbox(bbox2)):
        return 0.0
    
    # Calculate intersection
    x1 = max(bbox1['x'], bbox2['x'])
    y1 = max(bbox1['y'], bbox2['y'])
    x2 = min(bbox1['x'] + bbox1['width'], bbox2['x'] + bbox2['width'])
    y2 = min(bbox1['y'] + bbox1['height'], bbox2['y'] + bbox2['height'])
    
    if x2 <= x1 or y2 <= y1:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    union = calculate_bbox_area(bbox1) + calculate_bbox_area(bbox2) - intersection
    
    return intersection / union if union > 0 else 0.0
