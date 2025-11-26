# Complete Release Process - Quick Reference

**Document:** RELEASE_PROCESS.md  
**Location:** Project root directory  
**Last Updated:** November 26, 2025  
**Total Lines:** 904  

---

## What You Have

A **complete, step-by-step release process guide** that documents everything that was done for v1.0.2, ready to be applied to all future releases (v1.0.3, v1.1.0, v2.0.0, etc.).

---

## 10-Phase Process Overview

### Phase 1: Code Updates & Feature Implementation
**Purpose:** Add new features and update documentation  
**Time:** Variable (depends on features)  
**Sections:**
- Step 1.1: Implement Features
- Step 1.2: Update Version Numbers
- Step 1.3: Create Release Notes
- Step 1.4: Update Main README

---

### Phase 2: Setup Python Environment
**Purpose:** Prepare environment for building  
**Time:** 5 minutes (one-time if new system)  
**Sections:**
- Step 2.1: Configure Python Environment
- Step 2.2: Install Required Packages

---

### Phase 3: Build Executable
**Purpose:** Create CCPacker.exe from Python code  
**Time:** 3-5 minutes  
**Sections:**
- Step 3.1: Clean Previous Builds
- Step 3.2: Run PyInstaller
- Step 3.3: Verify Executable

**Key Output:** `dist/CCPacker.exe`

---

### Phase 4: Create Release Directory Structure
**Purpose:** Set up folders for packaging  
**Time:** 1 minute  
**Sections:**
- Step 4.1: Create Version Directories

**Result:**
```
release/v1.0.2/
├── CC-Packer_v1.0.2/
└── CC-Packer_v1.0.2_Source/
```

---

### Phase 5: Package Files
**Purpose:** Copy files to appropriate packages  
**Time:** 2 minutes  
**Sections:**
- Step 5.1: Copy Files to Binary Package
- Step 5.2: Copy Files to Source Package
- Step 5.3: Copy Supporting Documentation

---

### Phase 6: Create Zip Packages
**Purpose:** Compress packages for distribution  
**Time:** 2 minutes  
**Sections:**
- Step 6.1: Compress Binary Package
- Step 6.2: Compress Source Package
- Step 6.3: Verify Zip Files

**Result:**
- `CC-Packer_v1.0.2_Windows.zip` (~35 MB)
- `CC-Packer_v1.0.2_Source.zip` (~0.02 MB)

---

### Phase 7: Create Supporting Documentation
**Purpose:** Add comprehensive guides  
**Time:** Included in packaging  
**Sections:**
- Step 7.1: Create Release Documentation Files

**Files Created:**
- README_RELEASE.md
- DISTRIBUTION_READY.md
- MANIFEST.md
- INDEX.md

---

### Phase 8: Commit to Git
**Purpose:** Save changes to repository  
**Time:** 2 minutes  
**Sections:**
- Step 8.1: Stage Files for Commit
- Step 8.2: Commit Changes
- Step 8.3: Push to GitHub

---

### Phase 9: Create Release on GitHub
**Purpose:** Publish release on GitHub  
**Time:** 2 minutes  
**Sections:**
- Step 9.1: Navigate to Repository
- Step 9.2: Create Release Details
- Step 9.3: Finalize Release

---

### Phase 10: Distribution & Verification
**Purpose:** Verify and distribute release  
**Time:** 5 minutes  
**Sections:**
- Step 10.1: Verify Release Files
- Step 10.2: Optional - Additional Distribution

---

## Important Commands

### Build Executable
```powershell
& 'python_path' -m pyinstaller `
  --noconfirm `
  --onefile `
  --windowed `
  --name "CCPacker" `
  --clean `
  main.py
```

### Create Binary Zip
```powershell
Compress-Archive -Path "CC-Packer_v1.0.2" `
  -DestinationPath "CC-Packer_v1.0.2_Windows.zip" `
  -Force
```

### Create Source Zip
```powershell
Compress-Archive -Path "CC-Packer_v1.0.2_Source" `
  -DestinationPath "CC-Packer_v1.0.2_Source.zip" `
  -Force
```

### Stage & Commit
```powershell
git add README.md main.py merger.py RELEASE_NOTES_v1.0.2.md
git add -f release/v1.0.2/
git commit -m "Release v1.0.2: [Description]"
git push origin master
```

---

## Complete Checklist

See **RELEASE_PROCESS.md** section: "Complete Process Checklist"

Quick overview:
- Pre-Release: 12 items
- Build: 3 items
- Package: 10 items
- Git: 8 items
- Release: 10 items

**Total: 50+ checklist items to verify each release**

---

## Troubleshooting

See **RELEASE_PROCESS.md** section: "Troubleshooting Common Issues"

Covers:
- PyInstaller build failures
- Zip file issues
- Git push problems
- .gitignore conflicts
- And more solutions

---

## Version Numbering

**Format:** `MAJOR.MINOR.PATCH`

**Examples:**
- v1.0.2 (Current)
- v1.0.3 (Next patch)
- v1.1.0 (Next feature release)
- v2.0.0 (Major release)

**See RELEASE_PROCESS.md** for increment rules

---

## Timeline Estimate

| Phase | Time |
|-------|------|
| Code Updates | Variable |
| Environment | 5 min |
| Build | 3-5 min |
| Package | 2 min |
| Git | 2 min |
| Release | 2 min |
| Distribution | 5 min |
| **Total** | **15-30 min** |

---

## Files Modified/Created in v1.0.2

**Core Code:**
- ✅ `main.py` - Updated version to 1.0.2
- ✅ `merger.py` - Added FO4 localization support

**Documentation:**
- ✅ `README.md` - Updated with new features
- ✅ `RELEASE_NOTES_v1.0.2.md` - New file
- ✅ `RELEASE_PROCESS.md` - This process guide!

**Release Package:**
- ✅ `release/v1.0.2/CC-Packer_v1.0.2/` - Binary package
- ✅ `release/v1.0.2/CC-Packer_v1.0.2_Source/` - Source package
- ✅ Both packages include all documentation
- ✅ Zipped packages ready for distribution

---

## How to Use This Guide

### For v1.0.3 Release:

1. **Read Section 1:** Code Updates & Feature Implementation
   - Implement your changes
   - Update version to 1.0.3
   - Create RELEASE_NOTES_v1.0.3.md
   - Update README.md

2. **Read Section 2:** Setup Python Environment
   - Configure environment
   - Install dependencies

3. **Read Section 3:** Build Executable
   - Follow the steps exactly
   - Use commands provided

4. **Read Sections 4-6:** Package Creation
   - Create directories
   - Copy files
   - Create zip packages

5. **Read Sections 7-8:** Git Operations
   - Create documentation
   - Commit and push

6. **Read Sections 9-10:** Release & Distribution
   - Create GitHub release
   - Distribute if needed

7. **Use Checklist:** Verify nothing missed

---

## Reference Sections in Document

| Section | Purpose |
|---------|---------|
| **Overview** | Introduction to process |
| **Phase 1-10** | Detailed step-by-step |
| **Complete Checklist** | Verification for each release |
| **Troubleshooting** | Common issues & solutions |
| **Version Numbering** | How to version releases |
| **Documentation Files** | What gets created |
| **Key Commands** | Quick reference |
| **Tips** | Best practices |

---

## What Each Phase Produces

| Phase | Output | Size |
|-------|--------|------|
| 1 | Updated code & docs | N/A |
| 2 | Configured environment | N/A |
| 3 | CCPacker.exe | ~35 MB |
| 4 | Directory structure | N/A |
| 5 | Populated packages | N/A |
| 6 | Zip files | ~35 MB total |
| 7 | Documentation files | N/A |
| 8 | Git commit | N/A |
| 9 | GitHub release | Online |
| 10 | Verified release | ✅ Done |

---

## Important Notes

1. **Always follow the process sequentially** - Don't skip phases
2. **Use the exact commands provided** - They're tested and proven
3. **Check each phase output** - Verify before moving to next phase
4. **Use the checklist** - Don't rely on memory
5. **Keep releases in release/ folder** - For reference and backups
6. **Maintain version history** - Update RELEASE_NOTES consistently
7. **Test before releasing** - Especially for new features
8. **Document changes clearly** - Help future maintainers

---

## For Future Major Versions

If jumping to v2.0.0 or higher:

1. Update `__version__` constant if added to code
2. Update version badge format if needed
3. Update version pattern documentation
4. Consider updating build configuration
5. Update this reference guide if process changes

---

## Questions or Issues?

Refer to **RELEASE_PROCESS.md**:
- Check troubleshooting section first
- Read the specific phase in detail
- Look at command examples
- Review expected outputs

---

## Next Steps

1. ✅ Read this quick reference
2. ✅ Open RELEASE_PROCESS.md
3. ✅ Follow the 10-phase process for next release
4. ✅ Use the checklist to verify
5. ✅ Repeat for each release

---

**You now have a complete, documented release process ready for v1.0.3 and beyond!**

Document: RELEASE_PROCESS.md (904 lines)  
Location: Project root  
Created: November 26, 2025  
Status: ✅ Complete & Committed to GitHub
