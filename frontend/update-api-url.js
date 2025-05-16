// This script updates the API URL in the frontend build
// It's meant to be run during the Docker build process

const fs = require('fs');
const path = require('path');

// Get the API URL from environment variable or use default
const API_URL = process.env.VITE_API_URL || 'https://backend-service-url.a.run.app';

// Function to recursively find JS files in the dist directory
function findJsFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      findJsFiles(filePath, fileList);
    } else if (file.endsWith('.js')) {
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

// Find all JS files in the dist directory
const distDir = path.join(__dirname, 'dist');
const jsFiles = findJsFiles(distDir);

console.log(`Found ${jsFiles.length} JS files to process`);

// Replace localhost:8000 with the actual API URL
let replacementCount = 0;

jsFiles.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  
  // Replace any hardcoded localhost:8000 or localhost:8003 references
  const newContent = content
    .replace(/http:\/\/localhost:8000/g, API_URL)
    .replace(/http:\/\/localhost:8003/g, API_URL);
  
  if (content !== newContent) {
    fs.writeFileSync(file, newContent, 'utf8');
    replacementCount++;
    console.log(`Updated API URL in: ${file}`);
  }
});

console.log(`Updated API URL in ${replacementCount} files to: ${API_URL}`);
