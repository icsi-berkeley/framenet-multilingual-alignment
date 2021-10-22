import os
import time
import logging

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
		('chinesefn', 'zh'),
		('japanesefn', 'ja'),
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

		if db_name not in ["chinesefn", "swedishfn"]:
			attribute.id_matching(alignment)

		if db_name != "fnbrasil":
			attribute.name_matching(alignment)

		if db_name != "chinesefn":
			attribute.fe_matching(alignment)

		score_dfs = list(map(lambda x: x['df'], alignment.scores))
		df = score_dfs[0]

		if len(score_dfs) >= 2:
			df = df.add(score_dfs[1], fill_value=0)
		
		if len(score_dfs) == 3:
			df = df.add(score_dfs[2], fill_value=0)

		pairs = df[df == len(score_dfs)].stack().index.tolist()
		path = os.path.join('out', f'gold_{db_name}.txt')

		with open(path, 'w+') as fp:
			for frm1, frm2 in pairs:
				fp.write(f'{frm1.ljust(50)}{frm2}\n')

		logger.info(l2_fn.lang + " finished --- %s seconds ---" % (time.time() - start_time))

	logger.info("Process finished --- %s seconds ---" % (time.time() - global_time))
