// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import {promises as fs} from 'fs';
import path from 'path';


interface IHoudiniChatResult extends vscode.ChatResult {
    metadata: {
        command: string;
    }
}

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    const response_path = path.join(context.extensionPath, 'responses');

	// Use the console to output diagnostic information (console.log) and errors (console.error)
	// This line of code will only be executed once when your extension is activated
	console.log('Congratulations, your extension "hou-aibridge" is now active!');

	// The command has been defined in the package.json file
	// Now provide the implementation of the command with registerCommand
	// The commandId parameter must match the command field in package.json
	const disposable = vscode.commands.registerCommand('hou-aibridge.helloWorld', () => {
		// The code you place here will be executed every time your command is executed
		// Display a message box to the user
		vscode.window.showInformationMessage('Hello World from hou_aibridge!');
    });

    const chatHandler: vscode.ChatRequestHandler = async (
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ): Promise<IHoudiniChatResult> => {
        // Handle the chat request here
        console.log('Chat request received:', request);
        switch (request.command) {
            case 'list_node_types':
                const text = await fs.readFile(response_path + '/list_node_types.md', 'utf8');
                stream.markdown(text);
                break;
            default:
                stream.markdown(`Hello from zabob! This is a response to your request: 42.`);
        }
        return {
                metadata: {
                    command: 'zabob_response'
                }
            };
        };
    const zabob = vscode.chat.createChatParticipant('hou-aibridge.zabob', chatHandler);
    const icon = vscode.Uri.joinPath(context.extensionUri, 'zabob.jpg');
    zabob.iconPath = {
        light: icon,
        dark: icon
    };


    // Listen for text document changes
    vscode.workspace.onDidChangeTextDocument(event => {
        // Respond to changes here
        const editor = vscode.window.activeTextEditor;
        if (editor && event.document === editor.document) {
            // Your logic here
            console.log('Document changed:', event.document.fileName);
        }
    });

    // Optionally, listen for active editor changes
    vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor) {
            // Your logic here
            console.log('Active editor changed:', editor.document.fileName);
        }
    });

	context.subscriptions.push(disposable);
}

// This method is called when your extension is deactivated
export function deactivate() {}
;
