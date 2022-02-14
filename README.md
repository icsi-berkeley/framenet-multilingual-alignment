## Multilingual Framenet

If you want to experiment with ViToXF, our alignment visualization tool, you can download the most recent version under this repo Releases ([link](https://github.com/icsi-berkeley/framenet-multilingual-alignment/releases)). Please refer to the [user's guide](https://github.com/icsi-berkeley/framenet-multilingual-alignment/blob/master/ViToXFUserGuide.md) and if you have any question, feel free to open an issue. Thank you!

We're still working on this project, documentation is still not completed and we plan to add more languages and expand the techniques of the existing ones. 

## Preparing FrameNet data
 - Create a folder named "data" in the project's root
 - Inside "data", you should add a folder for each database you want to align. Some names, such as _bfn_, _chineseefn_ and _swedishfn_, are already associate to specific data loaders, _i.e._, they are expected to be in the formats provided by those responsible for those databases.
 - In any case, each database folder in data can be associated with a specific loader. To do that, navigate to [alignment/fnalign/loaders.py](https://github.com/icsi-berkeley/framenet-multilingual-alignment/blob/master/alignment/fnalign/loaders.py) and include your database folder name in the **supported_dbs** function. 
 - By default, you should consider using the **FNLoader**, as it supports the same format as the Berkeley FN 1.7 data release.

## Preparing MUSE data
 - To run alignment methods that use MUSE data, you need to also download the embeddings from [here](https://github.com/facebookresearch/MUSE)
 - Create and the _data/muse_ if it doesn't exists and move all the relevant _.vec_ files there.

## Running the alignment
 - Make sure you have **Conda** installed (https://docs.conda.io/en/latest/)
 - Run the following commands on the project's root:
 - `conda env create -f environment.yml`
 - `conda activate mlfn`
 - Before running the alignemnt, open [alignment/main.py](https://github.com/icsi-berkeley/framenet-multilingual-alignment/blob/master/alignment/main.py) and comment every line related to scoring techniques that you don't want to run (In a future version, this will be done using a CLI)
 - Finally, run:
 - `python3 ./alignment/main.py`

After running the output files will be in the **out** folder on the project's root.

## Running the visualizer
 - Make sure you have **node.js** (https://nodejs.org/en/) installed (v12 or higher) and **yarn** (https://yarnpkg.com/). 
- *cd* into the **visualizer** folder and run the following commands:
- `yarn install`
- `yarn start`
