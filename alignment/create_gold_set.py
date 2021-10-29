import os
import time
import logging
import pandas as pd

global_time = time.time()

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('alignment')

from fnalign.loaders import load
from fnalign.models import Alignment
from fnalign.alignment import attribute

if __name__ == "__main__":
	configs = [
		# ('chinesefn', 'zh'),
		# ('japanesefn', 'ja'),
		('frenchfn', 'fr'),
		('spanishfn', 'es'),
		('fnbrasil', 'pt'),
		('swedishfn', 'sv'),
		('salsa', 'de'),
		('dutchfn', 'nl'),
	]

	en_fn = load("bfn", "en")

	for db_name, lang in configs:
		start_time = time.time()

		l2_fn = load(db_name, lang)
		alignment = Alignment(en_fn, l2_fn)
		df = pd.DataFrame(0, index=alignment.en_frm['name'], columns=alignment.l2_frm['name'])

		if db_name != "fnbrasil":
			attribute.name_matching(alignment)
			df_score = alignment.scores[-1]["df"]
			df = df.add(df_score, fill_value=0)

		logger.info(f'     matching name count    = {len(df.loc[:, (df == len(alignment.scores)).sum() > 0].columns)}')

		if db_name != "chinesefn":
			attribute.fe_matching(alignment)
			df_score = alignment.scores[-1]["df"]
			df = df.add(df_score, fill_value=0)

		logger.info(f'     matching name/fe count = {len(df.loc[:, (df == len(alignment.scores)).sum() > 0].columns)}')

		if db_name not in ["chinesefn", "swedishfn"]:
			attribute.id_matching(alignment)
			df_score = alignment.scores[-1]["df"]
			df = df.add(df_score, fill_value=0)

		logger.info(f'     matching id count      = {len(df.loc[:, (df == len(alignment.scores)).sum() > 0].columns)}')
		logger.info(f'')

		pairs = df[df == len(alignment.scores)].stack().index.tolist()
		path = os.path.join('out', f'gold_{db_name}.txt')

		with open(path, 'w+') as fp:
			for frm1, frm2 in pairs:
				fp.write(f'{frm1.ljust(50)}{frm2}\n')

		logger.info(l2_fn.lang + " finished --- %s seconds ---" % (time.time() - start_time))

	logger.info("Process finished --- %s seconds ---" % (time.time() - global_time))
