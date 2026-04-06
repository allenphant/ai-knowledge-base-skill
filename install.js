const fs = require('fs');
const path = require('path');
const os = require('os');

// Paths to CLI skills directories
const geminiDir = path.join(os.homedir(), '.gemini', 'skills');
const claudeDir = path.join(os.homedir(), '.claude', 'skills');

const targetGeminiDir = path.join(geminiDir, 'ai-knowledge-base');
const targetClaudeDir = path.join(claudeDir, 'ai-knowledge-base');

console.log('📦 Installing ai-knowledge-base skill for both Gemini CLI and Claude Code...');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// Ensure parent directories exist
ensureDir(geminiDir);
ensureDir(claudeDir);
ensureDir(targetGeminiDir);
ensureDir(targetClaudeDir);

// Function to copy directory recursively
function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (let entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      ensureDir(destPath);
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

// Copy everything from the package root to both skill directories
const pkgDir = __dirname;
copyDir(pkgDir, targetGeminiDir);
copyDir(pkgDir, targetClaudeDir);

// -------------------------------------------------------------
// Update absolute paths in instructions.md dynamically
// -------------------------------------------------------------
function updateInstructionsPaths(targetSkillDir) {
  const instructionsPath = path.join(targetSkillDir, 'references', 'instructions.md');
  
  if (fs.existsSync(instructionsPath)) {
    let instructions = fs.readFileSync(instructionsPath, 'utf8');

    // Replace the placeholder with the actual absolute path to the skill directory
    // We use split/join for global replacement of a plain string
    instructions = instructions.split('{{SKILL_DIR}}').join(targetSkillDir);

    fs.writeFileSync(instructionsPath, instructions, 'utf8');
    return instructionsPath;
  }
  return null;
}

const geminiInstPath = updateInstructionsPaths(targetGeminiDir);
const claudeInstPath = updateInstructionsPaths(targetClaudeDir);

console.log('✅ ai-knowledge-base skill installed successfully!');
console.log('----------------------------------------------------');
console.log('📌 Next Steps:');
console.log('1. Verify your Obsidian Vault Path inside:');
console.log(`   - Gemini CLI: ${geminiInstPath}`);
console.log(`   - Claude Code: ${claudeInstPath}`);
console.log('2. Ensure Python, yt-dlp, and ffmpeg are installed for Mode A/B.');
console.log('3. Open your Agent CLI and type:');
console.log('   - Gemini CLI: /skill ai-knowledge-base');
console.log('   - Claude Code: /skill ai-knowledge-base');
console.log('----------------------------------------------------');