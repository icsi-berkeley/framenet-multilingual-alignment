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

MUSE_NMAX=200000
MUSE_EMBS = {}
LU_EMBS = {}

def get_muse_emb(lang, nmax=200000, cache=False):
	"""Instantiates a new :class:`MuseWordEmbedding` with language ``lang`` when needed,
	otherwise retrieves one from cache.

	:param lang: Language of the embedding.
	:type lang: str
	:param nmax: Maximum number of vectors to be loaded.
	:type nmax: int
	:param cache: Whether getting an embedding from cache should be considered.
	:type cache: bool
	:returns: An :class:`MuseWordEmbedding` object for ``lang``.
	:rtype: :class:`MuseWordEmbedding`
	"""
	if cache and lang in MUSE_EMBS:
		return MUSE_EMBS[lang]

	path = os.path.join('data', 'muse', f'wiki.multi.{lang}.vec')

	emb = MuseWordEmbedding(lang, 300)
	emb.load_from_file(path, nmax=nmax)

	if cache:
		MUSE_EMBS[lang] = emb

	return emb

def get_lu_emb(db_name, lang, cache=False):
	"""Instantiates a new :class:`LUEmbedding` with language ``lang`` when needed,
	otherwise retrieves one from cache.

	:param lang: FrameNet database name.
	:type lang: str
	:param lang: Language of the embedding.
	:type lang: str
	:param cache: Whether getting an embedding from cache should be considered.
	:type cache: bool
	:returns: An :class:`LUEmbedding` object for ``lang``.
	:rtype: :class:`LUEmbedding`
	"""
	if cache and lang in LU_EMBS:
		return LU_EMBS[lang]

	path = os.path.join('data', 'bert', f'{db_name}_lu_embs.json')

	emb = LUEmbedding(lang, 768)
	emb.load_from_file(path)

	if cache:
		LU_EMBS[lang] = emb

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
	]

	en_fn = load("bfn", "en")

	for db_name, lang in configs:
		start_time = time.time()

		l2_fn = load(db_name, lang)
		alignment = Alignment(en_fn, l2_fn)

		if db_name == "fnbrasil":
			attribute.id_matching(alignment)
		else:
			attribute.name_matching(alignment)

		if db_name != "chinesefn":
			attribute.fe_matching(alignment)

		if db_name != "salsa":
			wordnet.lu_matching(alignment)
			wordnet.synset_matching(alignment)

		if db_name not in ["chinesefn", "japanesefn"]:
			en_emb = get_muse_emb("en", nmax=MUSE_NMAX, cache=True)
			l2_emb = get_muse_emb(lang, nmax=MUSE_NMAX)

			if lang != 'sv':
				vector.fe_matching(alignment, en_emb, l2_emb)
				vector.fe_exact_matching(alignment, en_emb, l2_emb)
				
			if db_name in ["fnbrasil", "salsa"]:
				vector.fe_mixed_matching(alignment)

			vector.lu_muse_matching(alignment, en_emb, l2_emb, scoring_configs=[(5, 0.3), (3, 0.3)])
			vector.lu_mean_matching(alignment, en_emb, l2_emb)
			vector.def_matching(alignment, en_emb, l2_emb)

		if db_name in ["spanishfn", "fnbrasil"]:
			en_emb = get_lu_emb("bfn", "en", cache=True)
			l2_emb = get_lu_emb(db_name, lang)

			vector.lu_bert_matching(alignment, en_emb, l2_emb, scoring_configs=[(5, 0.3), (3, 0.3)])
			vector.lu_mean_matching(alignment, en_emb, l2_emb)

		alignment.dump(ignore_scores=set(["lu_muse"]))
		# alignment.dump()

		logger.info(l2_fn.lang + " finished --- %s seconds ---" % (time.time() - start_time))

	logger.info("Process finished --- %s seconds ---" % (time.time() - global_time))