# GitHub Repository Setup Guide for CC-Packer

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. **Repository name**: `CC-Packer`
3. **Description**: "Standalone tool to merge Fallout 4 Creation Club archives - Reduce plugin count and improve performance"
4. **Visibility**: Public
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Push Local Repository to GitHub

```bash
# Set the remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/jturnley/CC-Packer.git

# Push the code and tags
git push -u origin master
git push origin v1.0.0
```

## Step 3: Configure Repository Settings

### Topics (Repository Tags)
Add these topics to help users find your project:
- fallout4
- creation-club
- ba2
- modding
- archive-manager
- pyqt6
- python

### About Section
- Website: (leave empty or add if you have one)
- Description: "Standalone tool to merge Fallout 4 Creation Club archives - Reduce plugin count and improve performance"

## Step 4: Create GitHub Release

### Option A: Via Web Interface

1. Go to https://github.com/jturnley/CC-Packer/releases/new
2. **Tag**: Select `v1.0.0` from dropdown
3. **Release title**: `CC-Packer v1.0.0 - Initial Release`
4. **Description**: Copy contents from `RELEASE_NOTES_v1.0.md`
5. **Attach binaries**:
   - Build the release first: `build_release.bat`
   - Upload `release/v1.0/CC-Packer_v1.0_Windows.zip`
   - Upload `release/v1.0/CC-Packer_v1.0_Source.zip`
6. ✅ Check "Set as the latest release"
7. Click "Publish release"

### Option B: Via GitHub CLI

```bash
# Build the release packages first
build_release.bat

# Create the release
gh release create v1.0.0 \
  --title "CC-Packer v1.0.0 - Initial Release" \
  --notes-file RELEASE_NOTES_v1.0.md \
  release/v1.0/CC-Packer_v1.0_Windows.zip \
  release/v1.0/CC-Packer_v1.0_Source.zip
```

## Step 5: Build Release Packages

If you haven''t built the release packages yet:

```bash
# From the CC-Packer directory
build_release.bat
```

This will create:
- `release/v1.0/CC-Packer_v1.0_Windows.zip` (~35 MB)
- `release/v1.0/CC-Packer_v1.0_Source.zip` (~10 KB)

## Step 6: Verify Everything

- [ ] Repository visible at https://github.com/jturnley/CC-Packer
- [ ] README displays correctly with badges
- [ ] All files present (main.py, merger.py, etc.)
- [ ] v1.0.0 tag visible
- [ ] Release created with downloadable assets
- [ ] Topics/tags added for discoverability

## Step 7: Update BA2 Manager Repository

Go back to the BA2 Manager repository and:

1. Update README.md to reference CC-Packer as a separate project
2. Remove or update references to the CC_Packer subdirectory
3. Optionally: Remove the CC_Packer folder from BA2 Manager repo

## Optional: Add Repository Details

### Social Preview Image
Create a social preview image (1280x640px) showing:
- CC-Packer logo/name
- "Merge Fallout 4 Creation Club Archives"
- Screenshot of the GUI

Upload via: Settings > Social preview

### Enable Discussions
Settings > Features > Enable Discussions
- Great for community support and feature requests

### Branch Protection
Settings > Branches > Add branch protection rule
- Branch name pattern: `master`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass

## Repository URLs

After setup, your repository will be available at:
- **Main**: https://github.com/jturnley/CC-Packer
- **Releases**: https://github.com/jturnley/CC-Packer/releases
- **Issues**: https://github.com/jturnley/CC-Packer/issues
- **Clone URL**: https://github.com/jturnley/CC-Packer.git

## Download Links for README

After creating the release, you can add download links to your README:

```markdown
## Download

- [Windows Binary (v1.0.0)](https://github.com/jturnley/CC-Packer/releases/download/v1.0.0/CC-Packer_v1.0_Windows.zip)
- [Source Code (v1.0.0)](https://github.com/jturnley/CC-Packer/releases/download/v1.0.0/CC-Packer_v1.0_Source.zip)
```
