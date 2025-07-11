# Phase 2 Examples

This directory contains examples demonstrating the Phase 2 features of the Ollama-OpenAI proxy:

- **Tool Calling Support**: Function/tool calling capabilities
- **Multimodal Input**: Image input support alongside text

## Prerequisites

1. **Proxy Running**: The Ollama-OpenAI proxy should be running on `localhost:11434`
2. **Backend Model**: Configure a model that supports the features you want to test
3. **Dependencies**: Install required Python packages

```bash
# Basic requirements
pip install ollama

# For multimodal examples
pip install pillow
```

## Examples

### 1. Tool Calling Example (`tool_calling_example.py`)

Demonstrates how to define and use tools/functions with the proxy:

```bash
python tool_calling_example.py
```

**Features shown:**
- Function definition with JSON schema
- Tool invocation by the model
- Bidirectional translation between Ollama and OpenAI formats
- Multiple tool types (weather, math calculations)

**Sample function definition:**
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"}
            },
            "required": ["location"]
        }
    }
}]
```

### 2. Multimodal Example (`multimodal_example.py`)

Demonstrates sending images along with text messages:

```bash
python multimodal_example.py
```

**Features shown:**
- Single image analysis
- Multiple image comparison  
- Mixed image + text conversations
- Base64 image encoding
- Loading external image files

**Sample multimodal message:**
```python
messages = [{
    "role": "user",
    "content": "What do you see in this image?",
    "images": [base64_image_data]
}]
```

## Configuration

### Model Requirements

**For Tool Calling:**
- Use models that support function calling (e.g., GPT-4, Claude, etc.)
- Configure your backend to handle tool/function calls

**For Multimodal:**
- Use vision-capable models (e.g., GPT-4 Vision, Claude 3, etc.)
- Ensure your backend supports image inputs

### Proxy Configuration

Make sure your `.env` file is configured with appropriate backend settings:

```env
# Example for OpenAI
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key-here

# Example for other providers
# OPENAI_API_BASE_URL=https://api.anthropic.com/v1
# OPENAI_API_KEY=your-anthropic-key
```

### Model Mapping

Configure model mappings in your `model_mapping.json` to use familiar names:

```json
{
  "model_mappings": {
    "gpt-4": "gpt-4-1106-preview",
    "gpt-4-vision": "gpt-4-vision-preview",
    "claude": "claude-3-sonnet-20240229"
  }
}
```

## Expected Output

### Tool Calling Example Output

```
Phase 2 Tool Calling Example
========================================
=== Example 1: Weather Query ===
Model requested 1 tool calls:
  Function: get_weather
  Arguments: {'location': 'Tokyo'}
  Result: {'location': 'Tokyo', 'temperature': 22, 'unit': 'celsius', 'condition': 'sunny'}

=== Example 2: Math Calculation ===
Model requested 1 tool calls:
  Function: calculate_math
  Arguments: {'expression': '15 * 23 + 7'}
  Result: {'expression': '15 * 23 + 7', 'result': 352, 'success': True}
```

### Multimodal Example Output

```
Phase 2 Multimodal (Image) Input Example
=============================================
=== Example 1: Single Image Analysis ===
Model response: I can see a colorful image with geometric shapes. There's a red rectangle on the left side, a green circle on the right, and text that says "Sample Image" at the bottom.

=== Example 2: Multiple Images Comparison ===
Model response: The main differences between these images are the colors and shapes. The first image has a red rectangle and green circle, while the second has a blue circle and purple rectangle.
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure the proxy is running on port 11434
   - Check `curl http://localhost:11434/health`

2. **Model Not Found**
   - Verify your model mappings are correct
   - Check that the backend model exists

3. **Tool Calls Not Working**
   - Ensure you're using a model that supports function calling
   - Check that tools are properly formatted with JSON schema

4. **Image Processing Errors**
   - Verify images are properly base64 encoded
   - Check that you're using a vision-capable model
   - Ensure image size is within limits

5. **Missing Dependencies**
   ```bash
   pip install ollama pillow
   ```

### Debug Mode

Enable debug logging to see detailed request/response translation:

```env
LOG_LEVEL=DEBUG
DEBUG=true
```

## Next Steps

- Try modifying the examples with your own functions and images
- Integrate Phase 2 features into your existing applications
- Explore advanced use cases like multi-step tool workflows
- Combine tool calling with multimodal inputs for rich interactions

For more information, see the main [README.md](../../README.md) and [documentation](../../docs/).