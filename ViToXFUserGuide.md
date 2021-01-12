


> Written with [StackEdit](https://stackedit.io/).
> User Guide for ViToXF, the VIsualization TOol for Cross-linguistic alignment of FrameNets

## What is ViToXF?
Thank you for downloading ViToXF.  ViToXF is a graphical user interface (GUI) that enables you to interactively view alignments of frames across FrameNet projects in different languages. 
There are currently more than ten projects creating lexical resources based on Frame Semantics and, to some extent, the FrameNet project at ICSI in Berkeley. Because they were created independently, for different languages, and in different situations, the semantic frames created for each language also differ to some extent from the Berkeley FrameNet frames for English.  At the same time, there are strong similarities among the frames across languages and many researchers are interested how similar they are and how they differ.  

The Multilingual FrameNet (MLFN) project at ICSI, funded by NSF (#16NNNNNN),  has developed and implemented a number of algorithms to align frames across languages, and output files recording the alignments produced between Berkeley FrameNet (for English) and the FrameNet database for NNN of the other languages.  These files form the input for ViToXF.  By using ViToXF, you can see which frames are aligned across languages and how strong those alignments are.

## Getting started
### Installing ViToXF
In the folder "executables"  you have created by unpacking the .zip file, you will find three versions of the ViToXF software:
 - `FrameNet Alignment Visualizer 0.1.0.exe` for MS Windows systems
 - `FrameNet Alignment Visualizer 0.1.0.dmg` for Mac OS systems
 - `FrameNet Alignment Visualizer 0.1.0.AppImage` for Linux systems

Please follow the installation procedure for your operating system.  If you need detailed instructions for installing the program, please visit the web page for your system:
 - **Mac OS:** https://www.wikihow.com/Install-Software-from-Unsigned-Developers-on-a-Mac
 - **Windows:**
 - **Linux:** 
 When you unpacked the .zip file, you should also have created a folder called framenet-alignment, which contains the ViToXF data files from each language. The file names contain the date and time of creation, the name of the language, the letters "fn", and the extension .json, like this: 202006301121_spanishfn.json. 
 
### Basic operation
Launch ViToXF.  You will see the basic Vtx screen, with the message "No data to show" in the right column. 

(1) Click on the "Choose File" button entitled "Alignment file" at the top of the left column and find and choose the data file for one of the languages.  Some of these files are several hundred Mb, so they may take a little while to load. 
(2) Choose one of the scoring techniques from the dropdown menu entitled "Scoring technique". 
