# Troubleshooting Guide

This guide helps resolve common issues when working with the DnD Character Sheet project.

## Table of Contents
- [Stopping Running Processes](#stopping-running-processes)
- [Port Already in Use](#port-already-in-use)
- [Virtual Environment Issues](#virtual-environment-issues)
- [Browser Storage Issues](#browser-storage-issues)

## Stopping Running Processes

### "I have some processes running, how do I stop them?"

If you've started the Flask server or other background processes and need to stop them:

#### Quick Stop: Keyboard Interrupt
The easiest way is to press `Ctrl+C` in the terminal where the process is running. This sends a graceful shutdown signal.

#### Finding Running Processes

**Windows (PowerShell):**
```powershell
# Show all Python processes
Get-Process python | Format-Table -AutoSize

# Show processes with port information
netstat -ano | findstr "LISTENING"

# Find process using specific port (e.g., 8080)
netstat -ano | findstr :8080
```

**Linux/macOS (Bash):**
```bash
# Show all Python processes
ps aux | grep python | grep -v grep

# Show processes with port information
netstat -tuln | grep LISTEN

# Find process using specific port (e.g., 8080)
lsof -i :8080
```

#### Stopping Specific Processes

**Windows (PowerShell):**
```powershell
# Stop by Process ID (PID) - safest method
Stop-Process -Id <PID>

# Force stop if process is not responding
Stop-Process -Id <PID> -Force

# Stop all Python processes (USE WITH CAUTION - stops ALL Python)
Stop-Process -Name python
```

**Linux/macOS (Bash):**
```bash
# Stop by Process ID (PID) - safest method
kill <PID>

# Force stop if process is not responding
kill -9 <PID>

# Stop process on specific port
lsof -ti:8080 | xargs kill

# Force stop process on specific port
lsof -ti:8080 | xargs kill -9
```

### Example: Stopping Flask Server on Port 8080

**Windows:**
```powershell
# Find the process
$proc = netstat -ano | findstr :8080
# Extract PID from output and stop it
Stop-Process -Id <PID>
```

**Linux/macOS:**
```bash
# Find and stop in one command
lsof -ti:8080 | xargs kill
```

## Port Already in Use

### Error: "Address already in use" or "Port 8080 is already allocated"

This means another process is using the port you're trying to use.

**Solutions:**

1. **Stop the conflicting process** (see [Stopping Running Processes](#stopping-running-processes) above)

2. **Use a different port:**
   ```bash
   python backend.py --port 5001
   ```

3. **Find what's using the port:**
   
   Windows:
   ```powershell
   netstat -ano | findstr :<PORT>
   ```
   
   Linux/macOS:
   ```bash
   lsof -i :<PORT>
   ```

## Virtual Environment Issues

### "I can't activate the virtual environment"

**Windows PowerShell Execution Policy Error:**
```
Error: cannot be loaded because running scripts is disabled on this system
```

**Solution:**
```powershell
# Run as Administrator or set execution policy for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "pip install fails" or "Module not found"

**Solution:**
```bash
# Make sure venv is activated, then reinstall
pip install --upgrade pip
pip install -r requirements.txt
```

### "How do I exit/deactivate the virtual environment?"

**Solution:**
```bash
deactivate
```

## Browser Storage Issues

### "My character data disappeared"

**Possible causes:**
- Browser cache/data was cleared
- Using different browser or incognito mode
- localStorage was full

**Solutions:**
1. Check if you have exported JSON files in the `/exports/` directory
2. Import a recent backup using the "Import JSON" feature
3. Set up regular exports as backups

### "Storage is full"

The browser has limited localStorage space (typically 5-10 MB).

**Solutions:**
1. Use the "Cleanup Old Exports" feature in the app
2. Clear old log data (automatic with 60-day rolling window)
3. Export characters to JSON files and clear localStorage
4. Use browser's Clear Site Data feature if needed

## Flask Server Issues

### "Server won't start"

**Check these:**
1. Is Python installed? `python --version` or `python3 --version`
2. Is the virtual environment activated?
3. Are dependencies installed? `pip install -r requirements.txt`
4. Is the port available? (see [Port Already in Use](#port-already-in-use))

### "Can't access server from another device"

**Solution:**
Start server with host binding:
```bash
python backend.py --host 0.0.0.0 --port 8080
```

Then access from other devices using your computer's IP address:
```
http://<YOUR-IP-ADDRESS>:8080
```

Find your IP:
- Windows: `ipconfig`
- Linux/macOS: `ifconfig` or `ip addr`

## No Background Agents or Services

**Note:** This project does not include any background "agents" or daemon services. If you're looking to stop something:

1. **Flask Server**: Use `Ctrl+C` or process management commands above
2. **Python Scripts**: Use `Ctrl+C` or process management commands above
3. **GitHub Copilot**: This is a code assistant in your IDE, not part of the project
4. **GitHub Actions**: These run in the cloud, not on your local machine

If you see references to "agents" in other contexts, they likely refer to:
- IDE extensions (VS Code, GitHub Copilot, etc.)
- CI/CD runners in GitHub Actions
- Browser service workers (automatically managed by the browser)

## Still Having Issues?

1. Check the main [README](README.md) for setup instructions
2. Review the [Development Notes](README.md#development-notes) section
3. Create an issue on GitHub with:
   - Description of the problem
   - Steps to reproduce
   - Error messages (if any)
   - Operating system and Python version
