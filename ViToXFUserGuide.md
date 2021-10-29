


> Written with [StackEdit](https://stackedit.io/).
> User Guide for ViToXF, the VIsualization TOol for Cross-linguistic alignment of FrameNets

## What is ViToXF?
Thank you for downloading ViToXF.  ViToXF is a graphical user interface (GUI) that enables you to interactively view alignments of frames across FrameNet projects in different languages. 
There are currently more than ten projects creating lexical resources based on Frame Semantics and, to some extent, the FrameNet project at ICSI in Berkeley. Because they were created independently, for different languages, and in different situations, the semantic frames created for each language also differ to some extent from the Berkeley FrameNet frames for English.  At the same time, there are strong similarities among the frames across languages and many researchers are interested how similar they are and how they differ.  

The Multilingual FrameNet (MLFN) project at ICSI, funded by NSF (#1629989), has developed and implemented a number of algorithms to align frames across languages and created data files representing the alignments between the frames, lexical units, and frame elements of Berkeley FrameNet (for English) and the FrameNet database for six of the other languages.  These files form the input for ViToXF; using ViToXF, you can see which frames are aligned across languages and how strong those alignments are.  Some of the alignments are one-to-one but others are one-to-many or many-to-many. More information about the alignment techniques can be found in Baker and Lorenzi (2020) [Exploring Crosslinguistic Frame Alignment](https://www.aclweb.org/anthology/2020.framenet-1.11/).


## Getting started
### Installing ViToXF

When you unpacked the .zip file, you should  have created a folder called Data, which contains the ViToXF data files for each language. Most of the file names contain the date and time of creation, the name of the language, the letters "fn", and the extension .json, like this: 202006301121_spanishfn.json. For historical reasons, the file for Brasilian Portuguese is called 202101222058_fnbrasil.json, and the file for German is called 202101222119_salsa.json.
 

Unpacking the .zip file should also have created the files for three versions of the ViToXF software:
 - `FrameNet Alignment Visualizer 0.1.0.exe` for MS Windows systems
 - `FrameNet Alignment Visualizer 0.1.0.dmg` for Mac OS systems
 - `FrameNet Alignment Visualizer 0.1.0.AppImage` for Linux systems

Please follow the installation procedure for your operating system; details are available on the web page for your system:
 - **Mac OS:** https://www.wikihow.com/Install-Software-from-Unsigned-Developers-on-a-Mac
 - **Windows:** 
 - **Linux:** 
 
### Basic operation
Launch ViToXF.  You will see the basic Vtx screen, with the message "No data to show" in the right column. 

(1) Click on the "Browse" button under "Alignment file" at the top of the left column; find and choose the data file for one of the languages.  Some of these files are rather large, so they may take a little while to load.  When the file finishes loading, the names of the frames **in both languages** will appear (greyed out) and the drop-down under "Scoring technique" will become active.

(2) Choose one of the scoring techniques from the dropdown menu. 

(3) Check the boxes for one or more frames from the list of frames.  You can use the search function to find the names of frames of interest.

(4) A [Sankey diagram](https://en.wikipedia.org/wiki/Sankey_diagram) will appear in the right-hand column showing the frame alignments that meet the current constraints. Changes in the parameters of the alignment algorithm on the left will immediately appear in the graph at the right.

## Acknowledgements

We are grateful for the support of the U.S. National Science Foundation (NSF #1629989) which made this alignment project possible, and for their support of the FrameNet project over the years, beginning with a grant to Prof. Charles J. Fillmore in 1997.  We are also grateful to each of the collaborating FrameNet-related projects for providing us with their data.  We especially wish to acknowledge the work of Arthur Lorenzi, who built the release version of the software and compiled the alignment databases.  

The Spanish FrameNet project (PI: Carlos Subirats) has been developed at the Autonomous University of Barcelona (Spain) and the International Computer Science Institute (Berkeley, CA) in cooperation with the FrameNet Project.  They also wish to acknowledge previous funding provided by the Ministry of Economy and Competitiveness of Spain (Grants Nr. FFI2017-84460-P, FFI2014-56444-C2-1-P and FFI2011-23231), the Department of Science and Innovation (FFI2008-0875), and the Department of Science and Technology (TIC2002-01338). Additional funding has also been provided by the Fundación Comillas, the Department of Education (TSI2005-01200), and the Autonomous University of Barcelona (PNL2004-49 and PRP2006-04).

For further information on the FrameNet-related projects including in this alignment, please see 

https://framenet.icsi.berkeley.edu/fndrupal/framenets_in_other_languages
