## Multilingual Framenet

We're still working on this project, documentation is still not completed and we plan to add more languages and expand the techniques of the existing ones. Feel free to open issues if you have any question. Thank you!

## Running the alignment
 - Make sure you have **Conda** installed (https://docs.conda.io/en/latest/)
 - Copy all required data to a folder **data** on the root of the project
 - Run the following commands on the project's root:
 - `conda env create -f environment.yml`
 - `conda activate mlfn`
 - `python3 ./alignment/main.py`

After running the output files will be in the **out** folder on the project's root.

## Running the visualizer
 - Make sure you have **node.js** (https://nodejs.org/en/) installed (v12 or higher) and **yarn** (https://yarnpkg.com/). 
- *cd* into the **visualizer** folder and run the following commands:
- `yarn install`
- `yarn start`
