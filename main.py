import os
import time
global_time = time.time()

from fnalign.loaders import load
from fnalign.models import Alignment
from fnalign.alignment import attribute, muse, wordnet
from fnalign.embeddings import MuseWordEmbedding, BertWordEmbedding

MUSE_NMAX=200000
MUSE_EMBS = {}
BERT_EMBS = {}

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

def get_bert_emb(lang, cache=True):
	"""Instantiates a new :class:`BertWordEmbedding` with language ``lang`` when needed,
	otherwise retrieves one from cache.

	:param lang: Language of the embedding.
	:type lang: str
	:param cache: Whether getting an embedding from cache should be considered.
	:type cache: bool
	:returns: An :class:`BertWordEmbedding` object for ``lang``.
	:rtype: :class:`BertWordEmbedding`
	"""
	if cache and lang in BERT_EMBS:
		return BERT_EMBS[lang]

	path = os.path.join('data', 'bert', f'default_L-12_CLS_TOKEN.{lang}.vec')

	emb = BertWordEmbedding(lang, 768)
	emb.load_from_file(path)

	if cache:
		BERT_EMBS[lang] = emb

	return emb


if __name__ == "__main__":
	configs = [
		# ('bfn', 'en'),
		('chinesefn', 'zh'),
		('japanesefn', 'ja'),
		('frenchfn', 'fr'),
		('spanishfn', 'es'),
		('fnbrasil', 'pt'),
		('swedishfn', 'sv'),
		('salsa', 'de'),
	]

	# for db_name, lang in configs:
	# 	vocab = list(set(k for k,v in get_muse_emb(lang).word2id.items() if k.strip()))

	# 	emb = BertWordEmbedding(lang, 768)
	# 	emb.load_from_vocab(vocab)

	# 	path = os.path.join('data', 'bert', f'default_L-12_CLS_TOKEN.{lang}.vec')
	# 	emb.save_to_file(path)

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

		if lang not in ["zh", "ja"]:
			en_muse_emb = get_muse_emb("en", nmax=MUSE_NMAX, cache=True)
			l2_muse_emb = get_muse_emb(lang, nmax=MUSE_NMAX)

			if lang != 'sv':
				muse.fe_matching(alignment, en_muse_emb, l2_muse_emb)
				muse.fe_exact_matching(alignment, en_muse_emb, l2_muse_emb)
				
			if db_name in ["fnbrasil", "salsa"]:
				muse.fe_mixed_matching(alignment)

			muse.lu_matching(alignment, en_muse_emb, l2_muse_emb, scoring_configs=[(10, 0.3), (5, 0.3), (3, 0.3)])
			muse.lu_mean_matching(alignment, en_muse_emb, l2_muse_emb)
			muse.def_matching(alignment, en_muse_emb, l2_muse_emb)

			en_bert_emb = get_bert_emb("en", cache=True)
			l2_bert_emb = get_bert_emb(lang)

			muse.lu_matching(alignment, en_bert_emb, l2_bert_emb, scoring_configs=[(10, 0.3), (5, 0.3), (3, 0.3)], name="bert")

		alignment.dump(ignore_scores=set(["lu_muse"]))
		# alignment.dump()

		print(l2_fn.lang + " finished --- %s seconds ---" % (time.time() - start_time))

	print("Process finished --- %s seconds ---" % (time.time() - global_time))