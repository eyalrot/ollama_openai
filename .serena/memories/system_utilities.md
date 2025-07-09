# System Utilities (Linux)

## File System Commands
```bash
# List files and directories
ls -la              # List all files with details
ls -lh              # Human-readable file sizes
tree                # Tree view of directory structure (if installed)

# Navigate directories
cd /path/to/dir     # Change directory
pwd                 # Print working directory
cd ..               # Go up one directory
cd ~                # Go to home directory

# File operations
cp source dest      # Copy file
cp -r src/ dest/    # Copy directory recursively
mv old new          # Move/rename file
rm file             # Remove file
rm -rf dir/         # Remove directory recursively (careful!)
mkdir -p path/to/dir # Create directory with parents

# File viewing
cat file            # View entire file
less file           # View file with pagination
head -n 20 file     # View first 20 lines
tail -n 20 file     # View last 20 lines
tail -f file        # Follow file updates (logs)
```

## Search Commands
```bash
# Find files
find . -name "*.py"           # Find Python files
find . -type f -name "*test*" # Find files with 'test' in name
find . -type d -name "src"    # Find directories named 'src'

# Search in files
grep -r "pattern" .           # Recursive search
grep -rn "pattern" .          # With line numbers
grep -rl "pattern" .          # List files only
grep -i "pattern" file        # Case insensitive

# Ripgrep (faster alternative if installed)
rg "pattern"                  # Search recursively
rg -t py "pattern"           # Search only Python files
rg -i "pattern"              # Case insensitive
```

## Process Management
```bash
# View processes
ps aux              # All processes
ps aux | grep python # Python processes
top                 # Interactive process viewer
htop                # Better process viewer (if installed)

# Kill processes
kill PID            # Graceful termination
kill -9 PID         # Force kill
killall process_name # Kill by name

# Background jobs
command &           # Run in background
jobs                # List background jobs
fg %1               # Bring job 1 to foreground
bg %1               # Send job 1 to background
```

## Environment Variables
```bash
# View variables
env                 # All environment variables
echo $VAR_NAME      # Specific variable
printenv VAR_NAME   # Alternative

# Set variables
export VAR=value    # Set for current session
VAR=value command   # Set for single command

# Common variables
echo $PATH          # Executable search paths
echo $HOME          # Home directory
echo $USER          # Current user
echo $PWD           # Current directory
```

## Network Utilities
```bash
# Check connectivity
curl http://localhost:11434/health
wget -O- http://localhost:11434/health

# View network connections
netstat -tuln       # Listening ports
ss -tuln           # Modern alternative
lsof -i :11434     # What's using port 11434

# DNS lookup
nslookup domain.com
dig domain.com
```

## Permissions
```bash
# View permissions
ls -l file          # View file permissions

# Change permissions
chmod +x script.sh  # Make executable
chmod 755 file      # rwxr-xr-x
chmod 644 file      # rw-r--r--

# Change ownership
chown user:group file
```

## Archive Management
```bash
# Tar archives
tar -czf archive.tar.gz directory/  # Create compressed
tar -xzf archive.tar.gz             # Extract compressed
tar -tzf archive.tar.gz             # List contents

# Zip archives
zip -r archive.zip directory/        # Create zip
unzip archive.zip                    # Extract zip
unzip -l archive.zip                 # List contents
```