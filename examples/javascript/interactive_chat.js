#!/usr/bin/env node
/**
 * Interactive chat interface using Ollama JS SDK
 * Install: npm install ollama readline
 */

import { Ollama } from 'ollama';
import readline from 'readline';

// Initialize Ollama client
const ollama = new Ollama({ host: 'http://localhost:11434' });

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: '\nYou: '
});

// Conversation history
let messages = [
  {
    role: 'system',
    content: 'You are a helpful AI assistant. Keep responses concise and informative.'
  }
];

// Print welcome message
console.log('Ollama OpenAI Proxy - Interactive Chat');
console.log('Commands: /quit - exit, /clear - reset conversation, /model <name> - change model');
console.log('-'.repeat(60));

let currentModel = 'gpt-3.5-turbo';
console.log(`Using model: ${currentModel}`);

// Handle line input
rl.on('line', async (input) => {
  const trimmed = input.trim();
  
  // Handle commands
  if (trimmed.startsWith('/')) {
    const [command, ...args] = trimmed.slice(1).split(' ');
    
    switch (command) {
      case 'quit':
        console.log('Goodbye!');
        rl.close();
        process.exit(0);
        break;
        
      case 'clear':
        messages = [messages[0]]; // Keep system message
        console.log('Conversation cleared.');
        break;
        
      case 'model':
        if (args.length > 0) {
          currentModel = args.join(' ');
          console.log(`Switched to model: ${currentModel}`);
        } else {
          console.log(`Current model: ${currentModel}`);
        }
        break;
        
      default:
        console.log('Unknown command. Available: /quit, /clear, /model <name>');
    }
    
    rl.prompt();
    return;
  }
  
  // Skip empty input
  if (!trimmed) {
    rl.prompt();
    return;
  }
  
  // Add user message
  messages.push({ role: 'user', content: trimmed });
  
  try {
    // Show typing indicator
    process.stdout.write('\nAssistant: ');
    
    // Stream the response
    const stream = await ollama.chat({
      model: currentModel,
      messages: messages,
      stream: true
    });
    
    let fullResponse = '';
    
    for await (const chunk of stream) {
      if (chunk.message && chunk.message.content) {
        process.stdout.write(chunk.message.content);
        fullResponse += chunk.message.content;
      }
    }
    
    console.log(); // New line after response
    
    // Add assistant response to history
    messages.push({ role: 'assistant', content: fullResponse });
    
    // Keep conversation manageable (max 20 messages + system)
    if (messages.length > 21) {
      messages = [messages[0], ...messages.slice(-20)];
    }
    
  } catch (error) {
    console.error(`\nError: ${error.message}`);
    // Remove the failed user message
    messages.pop();
  }
  
  rl.prompt();
});

// Handle close event
rl.on('close', () => {
  console.log('\nChat session ended.');
  process.exit(0);
});

// Start the prompt
rl.prompt();