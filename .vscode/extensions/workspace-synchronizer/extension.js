// .vscode/extensions/daemon/extension.js
const vscode = require('vscode');
const { spawn } = require('child_process');

let daemon = null;
let output = null;

function activate() {
    output = vscode.window.createOutputChannel('Workspace Synchronizer');
    
    // Start daemon
    const root = vscode.workspace.workspaceFolders[0].uri.fsPath;
    daemon = spawn('uv', ['run', '-m', 'src.sync_workspace.main'], {
        cwd: root + '/scripts',
        env: { ...process.env, PYTHONUNBUFFERED: '1' }  // Force Python to flush output
    });
    
    daemon.stdout.on('data', data => output.append(data.toString()));
    daemon.stderr.on('data', data => output.append(data.toString()));
    daemon.on('close', code => {
        output.appendLine(`Daemon exited: ${code}`);
        daemon = null;
    });
    
    output.appendLine('Daemon started');
}

function deactivate() {
    if (daemon) daemon.kill();
}

module.exports = { activate, deactivate };