#!/usr/bin/env python3
"""
Phase 2 Feature: Multimodal (Image) Input Example

This example demonstrates how to send images along with text messages
using the Ollama-OpenAI proxy. The proxy handles the translation between
Ollama and OpenAI multimodal formats.
"""

import base64
import io
from ollama import Client
from PIL import Image, ImageDraw


def create_sample_image():
    """Create a simple sample image for demonstration purposes."""
    # Create a 400x300 image with a gradient background
    img = Image.new('RGB', (400, 300), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Draw some shapes
    draw.rectangle([50, 50, 150, 150], fill='red', outline='darkred')
    draw.ellipse([200, 100, 350, 200], fill='green', outline='darkgreen')
    draw.text((160, 250), "Sample Image", fill='black')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    image_data = base64.b64encode(buffer.getvalue()).decode()
    
    return image_data


def load_image_file(file_path: str) -> str:
    """Load an image file and convert it to base64."""
    try:
        with open(file_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        return image_data
    except FileNotFoundError:
        print(f"Warning: Image file '{file_path}' not found. Using sample image instead.")
        return create_sample_image()


def main():
    """Demonstrate multimodal input with the Ollama-OpenAI proxy."""
    
    # Initialize client (proxy running on default port)
    client = Client(host='http://localhost:11434')
    
    print("=== Example 1: Single Image Analysis ===")
    try:
        # Create or load an image
        image_data = create_sample_image()
        
        response = client.chat(
            model='gpt-4-vision-preview',  # Vision-capable model
            messages=[
                {
                    "role": "user",
                    "content": "What do you see in this image? Describe the colors, shapes, and any text.",
                    "images": [image_data]
                }
            ]
        )
        
        print(f"Model response: {response['message']['content']}")
    
    except Exception as e:
        print(f"Error in Example 1: {e}")
    
    print("\n" + "="*50 + "\n")
    
    print("=== Example 2: Multiple Images Comparison ===")
    try:
        # Create two different sample images
        image1 = create_sample_image()
        
        # Create a second image with different shapes
        img2 = Image.new('RGB', (400, 300), color='lightyellow')
        draw2 = ImageDraw.Draw(img2)
        draw2.ellipse([50, 50, 150, 150], fill='blue', outline='darkblue')
        draw2.rectangle([200, 100, 350, 200], fill='purple', outline='darkpurple')
        draw2.text((160, 250), "Image 2", fill='black')
        
        buffer2 = io.BytesIO()
        img2.save(buffer2, format='JPEG')
        image2 = base64.b64encode(buffer2.getvalue()).decode()
        
        response = client.chat(
            model='gpt-4-vision-preview',
            messages=[
                {
                    "role": "user",
                    "content": "Compare these two images. What are the differences in colors and shapes?",
                    "images": [image1, image2]
                }
            ]
        )
        
        print(f"Model response: {response['message']['content']}")
    
    except Exception as e:
        print(f"Error in Example 2: {e}")
    
    print("\n" + "="*50 + "\n")
    
    print("=== Example 3: Image + Text Conversation ===")
    try:
        # Start with an image
        image_data = create_sample_image()
        
        # First message with image
        response1 = client.chat(
            model='gpt-4-vision-preview',
            messages=[
                {
                    "role": "user",
                    "content": "What shapes do you see in this image?",
                    "images": [image_data]
                }
            ]
        )
        
        print(f"First response: {response1['message']['content']}")
        
        # Follow-up question (text only)
        response2 = client.chat(
            model='gpt-4-vision-preview',
            messages=[
                {
                    "role": "user",
                    "content": "What shapes do you see in this image?",
                    "images": [image_data]
                },
                response1['message'],  # Assistant's previous response
                {
                    "role": "user",
                    "content": "What colors are those shapes?"
                }
            ]
        )
        
        print(f"Follow-up response: {response2['message']['content']}")
    
    except Exception as e:
        print(f"Error in Example 3: {e}")
    
    print("\n" + "="*50 + "\n")
    
    print("=== Example 4: Loading External Image ===")
    try:
        # Try to load an external image file
        # You can replace this with any image file path
        external_image = load_image_file("sample.jpg")  # Will use sample if not found
        
        response = client.chat(
            model='gpt-4-vision-preview',
            messages=[
                {
                    "role": "user",
                    "content": "Analyze this image and tell me what you observe.",
                    "images": [external_image]
                }
            ]
        )
        
        print(f"Model response: {response['message']['content']}")
    
    except Exception as e:
        print(f"Error in Example 4: {e}")


if __name__ == "__main__":
    print("Phase 2 Multimodal (Image) Input Example")
    print("=" * 45)
    print("This example demonstrates sending images with text messages.")
    print("Make sure the Ollama-OpenAI proxy is running on localhost:11434")
    print("and configured with a vision-capable model.\n")
    
    # Check if PIL is available
    try:
        from PIL import Image, ImageDraw
        main()
    except ImportError:
        print("Error: PIL (Pillow) is required for this example.")
        print("Install with: pip install pillow")
        print("\nAlternatively, you can modify the example to use your own base64-encoded images.")