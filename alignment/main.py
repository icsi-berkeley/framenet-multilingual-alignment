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
from fnalign.alignment import attribute, vector, wordnet
from fnalign.embeddings import MuseWordEmbedding, LUEmbedding
from fnalign.evaluation import gold_scores

MUSE_NMAX=200000
MUSE_EMBS = {}

def get_muse_emb(lang, cache=False):
	"""Instantiates a new :class:`MuseWordEmbedding` with language ``lang`` when needed,
	otherwise retrieves one from cache.

	:param lang: Language of the embedding.
	:type lang: str
	:param cache: Whether getting an embedding from cache should be considered.
	:type cache: bool
	:returns: An :class:`MuseWordEmbedding` object for ``lang``.
	:rtype: :class:`MuseWordEmbedding`
	"""
	if cache and lang in MUSE_EMBS:
		return MUSE_EMBS[lang]

	path = os.path.join('data', 'muse', f'wiki.{lang}.align.vec')

	emb = MuseWordEmbedding(lang, 300)
	emb.load_from_file(path, nmax=MUSE_NMAX)

	if cache:
		MUSE_EMBS[lang] = emb

	return emb

def get_lu_emb(db_name, lang, en=False):
	"""Instantiates a new :class:`LUEmbedding` with language ``lang`` when needed,
	otherwise retrieves one from cache.

	:param lang: FrameNet database name.
	:type lang: str
	:param lang: Language of the embedding.
	:type lang: str
	:param en: Should return the english embeddings aligned to ``db_name``.
	:type en: bool
	:returns: An :class:`LUEmbedding` object for ``lang``.
	:rtype: :class:`LUEmbedding`
	"""
	if en:
		path = os.path.join('data', 'bert', f'{db_name}_en_lu_embs.json')
	else:
		path = os.path.join('data', 'bert', f'{db_name}_lu_embs.json')

	emb = LUEmbedding(lang, 768)
	emb.load_from_file(path)

	return emb


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

		attribute.fe_matching(alignment, core_only=False)

		wordnet.lu_matching(alignment)
		wordnet.synset_matching(alignment)

		# MUSE techniques
		if db_name != "japanesefn":
			en_emb = get_muse_emb("en", cache=True)
			l2_emb = get_muse_emb(lang)

			if db_name not in ["chinesefn", "swedishfn"]:
				vector.fe_matching(alignment, en_emb, l2_emb)
				vector.fe_exact_matching(alignment, en_emb, l2_emb)
				
			if db_name in ["fnbrasil", "salsa"]:
				vector.fe_mixed_matching(alignment)

			vector.lu_muse_matching(alignment, en_emb, l2_emb, scoring_configs=[(5, 0.3)])
			vector.lu_mean_matching(alignment, en_emb, l2_emb)
			vector.def_matching(alignment, en_emb, l2_emb)


		# BERT techniques
		if db_name != "chinesefn":
			en_emb = get_lu_emb(db_name, lang, en=True)
			l2_emb = get_lu_emb(db_name, lang)

			vector.lu_bert_matching(alignment, en_emb, l2_emb, scoring_configs=[(5, 0.3)])
			vector.lu_mean_matching(alignment, en_emb, l2_emb, 'bert')

		# gold_scores(alignment)

		# alignment.dump(ignore_scores=set(["lu_muse"]))
		alignment.dump()

		logger.info(l2_fn.lang + " finished --- %s seconds ---" % (time.time() - start_time))

	logger.info("Process finished --- %s seconds ---" % (time.time() - global_time))