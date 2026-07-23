# CC-Packer v3.2.1 Release Notes

**Release Date:** July 22, 2026

## 🎉 Patch Release: Stricter CC Detection & Faster Verification

Version 3.2.1 finalizes the move to strict `CCList.txt`-based detection (begun in v3.2.0) and optimizes the post-extraction verification pass so large Creation Club libraries process faster. This is a maintenance/performance release with no changes to the user-facing workflow.

## ✨ Highlights

### Strict CCList.txt Detection (v3.2.0)

- **No More Glob Fallback**: The legacy `cc*.ba2`/`cc*.esl` glob detection has been removed entirely. CC content is matched strictly against the bundled `CCList.txt`, so only official Creation Club items are ever backed up, merged, or repacked.
- **Bundled Authoritative List**: `CCList.txt` is a tracked file and is packaged inside the executable via `CCPacker.spec`, so compiled builds detect CC content exactly as the source does. (This closes the v3.1 gap where a build missing the bundled list could silently fall back to glob matching.)
- **Existing-Content Scan Aligned**: The check for already-present unpacked CC content also validates against `CCList.txt` rather than globbing.

### Faster Extraction Verification (v3.2.1)

- **O(n²) → O(n)**: Archives extract cumulatively into one shared directory. The post-extraction verification previously did a full recursive file **count** after *every* archive, so the walk grew with each item. It now short-circuits on the first extracted file — a presence check, which is all the verification ever used.
- **Minor Repack Optimization**: The Main-archive step tests for content with `any()` instead of building the full recursive file list.

## 🔧 Technical Improvements

- Rewrote `_verify_extraction` to use `any(...)` short-circuiting and corrected its docstring, which had described archive header/metadata validation the method does not perform.
- Replaced `list(dir.rglob("*"))` emptiness tests with `any(dir.rglob("*"))`.
- Removed the now-unreachable mixed-content confirmation dialog path.

## 🐛 Bug Fixes

- **Detection Accuracy in Builds**: Compiled builds no longer risk falling back to `cc*` glob detection; the authoritative `CCList.txt` is always bundled.

## 📦 What's Included

- `CCPacker.exe` - Main application v3.2.1
- `bsarch.exe` - Archive tool (bundled)
- `CCList.txt` - Official Creation Club file registry (bundled)
- `BSARCH_LICENSE.txt` - BSArch MPL 2.0 license
- `LICENSE` - CC-Packer MIT license
- `README.md` - Complete documentation

## 📋 Requirements

- Windows 10/11 (64-bit)
- Fallout 4 with Creation Club content
- No external tools required (bsarch.exe bundled)

## 🔄 v3.1.0 → v3.2.1 Upgrade

1. **Simple Update**: Download the new executable and replace the old one
2. **Data Preserved**: Existing backups and configurations are unaffected
3. **No Migration Needed**: No additional steps required to upgrade

## 📊 Version History

### v3.2.1 (July 22, 2026)

- Faster post-extraction verification (short-circuit instead of full recount)
- Minor repack emptiness-check optimization
- Corrected `_verify_extraction` documentation

### v3.2.0 (July 22, 2026)

- Strict `CCList.txt` detection; removed `cc*` glob fallback
- Bundled `CCList.txt` in the build via `CCPacker.spec`
- Removed unreachable mixed-content dialog path

### v3.1.0 (February 12, 2026)

- Limited CC detection to CCList.txt entries
- Silent background processing for packing operations
- Automatic restore & repack for mixed packed/unpacked content

### v3.0.0 (February 10, 2026)

- Content integrity and orphaned CC detection
- Automatic cleanup of incomplete CC downloads

## 📞 Support

For issues, questions, or feature requests:

- Open an issue on GitHub
- Check the README.md for detailed documentation
- Review RELEASE_NOTES_v3.1.0.md and earlier for historical context

---

**Release Type**: Patch Release (Maintenance/Performance)  
**Backward Compatibility**: Fully compatible with v3.2.0, v3.1.0, and earlier  
**Breaking Changes**: None
