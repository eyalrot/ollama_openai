#!/usr/bin/env node
/**
 * Basic usage example with the Ollama JavaScript SDK
 * Install first: npm install ollama
 */

import { Ollama } from 'ollama';

// Initialize client with proxy URL
const ollama = new Ollama({ host: 'http://localhost:11434' });

// Example 1: Simple generation
async function simpleGeneration() {
  console.log('=== Simple Generation ===');
  
  const response = await ollama.generate({
    model: 'gpt-3.5-turbo',
    prompt: 'Explain the concept of recursion in programming',
    stream: false
  });
  
  console.log('Response:', response.response);
  console.log('Tokens used:', response.eval_count || 'N/A');
}

// Example 2: Streaming generation
async function streamingGeneration() {
  console.log('\n=== Streaming Generation ===');
  
  const stream = await ollama.generate({
    model: 'gpt-3.5-turbo',
    prompt: 'Write a JavaScript function to reverse a string',
    stream: true
  });
  
  process.stdout.write('Response: ');
  for await (const chunk of stream) {
    process.stdout.write(chunk.response);
  }
  console.log('\n');
}

// Example 3: Chat with conversation history
async function chatExample() {
  console.log('=== Chat Example ===');
  
  const messages = [
    {
      role: 'system',
      content: 'You are a helpful JavaScript tutor.'
    },
    {
      role: 'user',
      content: 'What is the difference between let and const?'
    }
  ];
  
  const response = await ollama.chat({
    model: 'gpt-3.5-turbo',
    messages: messages,
    stream: false
  });
  
  console.log('Assistant:', response.message.content);
}

// Example 4: List available models
async function listModels() {
  console.log('\n=== Available Models ===');
  
  try {
    const models = await ollama.list();
    console.log('Models:', models.models.map(m => m.name).join(', '));
  } catch (error) {
    console.error('Error listing models:', error.message);
  }
}

// Example 5: Error handling
async function errorHandling() {
  console.log('\n=== Error Handling Example ===');
  
  try {
    // Try with a non-existent model
    await ollama.generate({
      model: 'non-existent-model',
      prompt: 'This should fail'
    });
  } catch (error) {
    console.log('Expected error:', error.message);
  }
}

// Main execution
async function main() {
  try {
    await simpleGeneration();
    await streamingGeneration();
    await chatExample();
    await listModels();
    await errorHandling();
  } catch (error) {
    console.error('Unexpected error:', error);
    process.exit(1);
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}