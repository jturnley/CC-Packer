# Archive2.exe Command Line Arguments

This document lists the command line arguments for `Archive2.exe`, the tool used to pack and unpack BA2 archives for Fallout 4.

## Usage

```bash
Archive2 <archive, files/folders> [<arguments>]
```

- `archive`: Specifies the archive to open (for extracting/opening an archive).
- `files/folders`: Specifies the files and folders to open (for making an archive, comma-delimited).

## Arguments

| Argument | Short | Description |
| :--- | :--- | :--- |
| `-sourceFile=<string>` | `-s` | Sets the source file to find contents to archive. Quotes required if spaces are involved. |
| `-excludeFile=<string>` | | Sets the file that lists files not to archive. Quotes required if spaces are involved. |
| `-create=<string>` | `-c` | Tells archiver to create an archive with the specified name. Quotes required if spaces are involved. |
| `-extract=<string>` | `-e` | Tells the archiver to extract an archive to the specified folder. Quotes required if spaces are involved. |
| `-createSourceFile=<string>` | `-csf` | Tells the archiver to create a source file from an archive to the specified folder. Quotes required if spaces are involved. |
| `-root=<string>` | `-r` | Tells the archiver what path to use for the archive root (instead of looking for a data folder). Quotes required if spaces are involved. |
| `-format=<General\|DDS\|XBoxDDS>` | `-f` | Sets the archive format. Default is `General`. |
| `-compression=<None\|Default\|XBox>` | | Sets the file compression settings. Default is `Default`. |
| `-count=<unsigned int>` | | Sets the archive count to make. Default is `0`. |
| `-maxSizeMB=<unsigned int>` | `-sMB` | Sets the maximum archive size in megabytes. Default is `0`. |
| `-maxChunkCount=<unsigned int>` | `-mch` | Sets the maximum number of chunks to use in a file. Default is `4`. |
| `-singleMipChunkX=<unsigned int>` | `-mipX` | Sets the X component of the minimum size a mip should be to have its own chunk. Default is `512`. |
| `-singleMipChunkY=<unsigned int>` | `-mipY` | Sets the Y component of the minimum size a mip should be to have its own chunk. Default is `512`. |
| `-nostrings` | | Does not write a string table to the archive. |
| `-quiet` | `-q` | Does not report progress or success (only failures). |
| `-tempFiles` | | Tells the archiver to use temporary files instead of loading chunks into memory. Slower, but reduces memory usage. |
| `-cleanup` | | Cleans up chunk temp folder on launch (do not use when multiple copies are running). |
| `-includeFilters=??` | | A list of regular expressions for file inclusion. |
| `-excludeFilters=??` | | A list of regular expressions for file exclusion. |
| `-?` | | Prints usage information. |

## Notes

- **Compression**: For sound files (`.xwm`, `.wav`, `.fuz`), it is recommended to use `-compression=None` to avoid playback issues in-game.
- **Format**: Use `-format=DDS` for texture archives to optimize them for the game engine. Use `-format=General` for everything else (meshes, scripts, sounds, etc.).
