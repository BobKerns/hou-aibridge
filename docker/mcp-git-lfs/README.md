# MCP Git Server with Git LFS Support

This Docker image extends the official `mcp/git` image to include Git LFS support.

## Problem

The standard `mcp/git` Docker image doesn't include `git-lfs`, which causes Git hooks to fail when working with repositories that use Git LFS for large files (like `.psd` files and databases).

## Solution

This custom image adds `git-lfs` to the base `mcp/git` image, allowing Git LFS hooks to work properly.

## Building

```bash
cd /Users/rwk/p/zabob/docker/mcp-git-lfs
./build.sh
```

## Usage

Update your Claude Desktop MCP configuration:

**Before:**
```json
"git": {
    "command": "docker",
    "args": ["run", "--rm", "-i", "--mount", "type=bind,src=/Users/rwk/p,dst=/Users/rwk/p", "mcp/git"]
}
```

**After:**
```json
"git": {
    "command": "docker",
    "args": ["run", "--rm", "-i", "--mount", "type=bind,src=/Users/rwk/p,dst=/Users/rwk/p", "mcp/git-lfs"]
}
```

## Verification

After building and updating the config, Git LFS operations should work without errors in MCP Git commands.
