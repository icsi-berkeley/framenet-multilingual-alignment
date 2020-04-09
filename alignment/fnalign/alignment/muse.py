"""This module contains a collection of alignment algorithms that are based on
MUSE: Multilingual Unsupervised and Supervised Embeddings.

.. moduleauthor:: Arthur Lorenzi Almeida <lorenzi.arthur@gmail.com>
"""
import io
import os
import re
import itertools
from collections import defaultdict
import numpy as np
from scipy.stats import rankdata
from scipy.spatial.distance import cosine

from ..embeddings import SearchIndex

FE_SPECIAL_CHAR_RE = re.compile(r'[\[\]\(\)\/\-\*\'\.\?!\d:",;_]')

def cosine_sim(a, b):
	"""Computes the cosine sim between two vectors.

	:param a: First vector.
	:type a: :class:`numpy.ndarray`
	:param b: Second vector.
	:type b: :class:`numpy.ndarray`s
	"""
	return (2 - cosine(a, b)) / 2

def lu_scores(alignment, lu_vecs, K, thres):
	"""Given ``alignemnt`` and ``lu_vecs``, uses ``K`` and ``thres`` to determine
	the neighborhood of each LU and and computes the score of each frame pair
	based on the count of LUs that have any of its neighbors on the second frame.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:param lu_vecs:
		A mapping of LU names to its neighborhood where vectors are tuples
		containing distance to the LU and the neighbor id.
	:type lu_vecs: list(tuple(float, int))
	:param K: The number of neighbors to be considered for scoring
	:type K: int
	:param thres: A distance threshold to consider vectors as neighbors.
	:type thres: float
	"""
	# Computing frame vectors based on nearest neighbors filters
	vec_sets = {
		k: set(i for d, i in v[:K] if d > thres)
		for k, v in lu_vecs.items()
	}

	frm_vecs = defaultdict(set)
	for _, row in alignment.frm.iterrows():
		frame = row["obj"]
		for lu in frame.lus:
			if lu.name in vec_sets:
				frm_vecs[frame.gid].update(vec_sets[lu.name])

	# Scoring
	scores = []
	for frame, other in alignment.pairs():
		if len(frame.lus) == 0:
			scores.append(0)
		else:
			scores.append(len(frm_vecs[frame.gid] & frm_vecs[other.gid]) / len(frame.lus))
	
	return scores

def infer_vec_fe(text, emb):
	"""Tokenizes the text from a FE name or definition (``text``) and infers its
	vector using ``emb``.

	:param text: The FE name or definition.
	:type text: str
	:param emb: The word embedding to be used.
	:type emb: class:`Embedding`
	:returns: The vector for ``text``.
	:rtype: class:`numpy.ndarray`
	"""
	if text:
		clean_def = FE_SPECIAL_CHAR_RE.sub(" ", text)
		clean_def = clean_def.lower()

		return emb.infer_vector(clean_def, ignore_unk=True)
	else:
		return None

def set_fe_vecs(alignment, en_emb, l2_emb, name_vecs=False):
	"""Computes vectors for FE definitions and names (if ``name_vecs`` is True)
	and stores it as a resource in ``alignment```.

	:param alignment: The alignment object.
	:type alignment: :class:`Alignment`
	:param en_emb: English word embedding.
	:type en_emb: :class:`Embedding`
	:param l2_emb: L2 word embedding.
	:type l2_emb: :class:`Embedding`
	:param name_vecs: If FE name vectors should be computed.
	:type name_vecs: bool
	"""
	cache = {}

	if "fe_def_vecs" not in alignment.resources:
		def_vecs = {}

		for frm in alignment.frm["obj"]:
			def_vecs[frm.gid] = {}
			emb = en_emb if frm.fe_lang == "en" else l2_emb
			for fe in frm.core_fes():
				if fe.definition in cache:
					def_vecs[frm.gid][fe.name] = cache[fe.definition]
				else:
					vec = infer_vec_fe(fe.definition, emb)
					if vec is not None:
						cache[fe.definition] = vec
						def_vecs[frm.gid][fe.name] = cache[fe.definition]

		alignment.resources["fe_def_vecs"] = def_vecs

	if "fe_name_vecs" not in alignment.resources and name_vecs:
		name_vecs = {}

		for frm in alignment.frm["obj"]:
			name_vecs[frm.gid] = {}
			emb = en_emb if frm.fe_lang == "en" else l2_emb
			for fe in frm.core_fes():
				if fe.name in cache:
					name_vecs[frm.gid][fe.name] = cache[fe.name]
				else:
					vec = infer_vec_fe(fe.name, emb)
					if vec is not None:
						cache[fe.name] = vec
						name_vecs[frm.gid][fe.name] = cache[fe.name]

		alignment.resources["fe_name_vecs"] = name_vecs


def exact_fe_score(frame, other, def_vecs):
	"""Computes the alignment score between ``frame`` and ``other`` considering
	exact frame matches weighted by the cosine similarity of their definitions.

	:param frame: Frame object.
	:type frame: class:`Frame`
	:param other: Other frame object.
	:type other: class:`Frame`
	:param def_vecs: FE definition vectors dictionary.
	:type def_vecs: dict
	:returns: The alignment score between the frame pair.
	:rtype: float
	"""
	en_def = def_vecs[frame.gid]
	l2_def = def_vecs[other.gid]

	if len(en_def.keys()) == 0 or len(l2_def.keys()) == 0:
		return 0
	else:
		inter = en_def.keys() & l2_def.keys()
		sim = map(lambda x: cosine_sim(en_def[x], l2_def[x]), inter)

		return sum(sim) / len(en_def.keys() | l2_def.keys())


def fe_score(frame, other, def_vecs, name_vecs):
	"""Computes the alignment score between ``frame`` and ``other`` by
	multiplying the cosine similarities of names and definitions of each FE pair
	and averaging all.

	:param frame: Frame object.
	:type frame: class:`Frame`
	:param other: Other frame object.
	:type other: class:`Frame`
	:param def_vecs: FE definition vectors dictionary.
	:type def_vecs: dict
	:param def_vecs: FE name vectors dictionary.
	:type def_vecs: dict
	:returns: The alignment score between the frame pair.
	:rtype: float
	"""
	en_def_vecs = def_vecs[frame.gid]
	l2_def_vecs = def_vecs[other.gid]
	en_name_vecs = name_vecs[frame.gid]
	l2_name_vecs = name_vecs[other.gid]
	en_fes = (en_def_vecs.keys() & en_name_vecs.keys())
	l2_fes = (l2_def_vecs.keys() & l2_name_vecs.keys())

	if len(en_fes) == 0 or len(l2_fes) == 0:
		return 0

	sims = [
		cosine_sim(en_name_vecs[x], l2_name_vecs[y])
		*
		cosine_sim(en_def_vecs[x], l2_def_vecs[y])
		for x, y in itertools.product(en_fes, l2_fes)
	]

	return sum(sims)/len(sims)


def lu_matching(alignment, en_emb, l2_emb, scoring_configs, name="muse"):
	"""Computes scores of each pair of frames on the alignment based on two
	different aligned word embeddings.

	TODO: move this method to another file since it can be used for vectors other
	than MUSE.

	This method consists of finding for each lexical unit in english frames its
	embedding and the 5 nearest neighbor of said embedding in the l2 vector set.
	The score of each alignment between a pair of frames is defined by the count
	of LUs of the l2 frame in the neighborhood the english frame LUs divided by
	the english frame LU count. Each tuple in ``scoring_configs`` defines the
	neighborhood based on a int value for maximum size and a float value as the
	threshold distance to be considered a neighbor.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:param en_emb: An :class:`WordEmbedding`instance for english.
	:type en_emb: :class:`WordEmbedding`
	:param l2_emb: An :class:`WordEmbedding`instance for l2.
	:type l2_emb: :class:`WordEmbedding`
	:param scoring_configs:
		A list of scoring config tuples containing a int value for K and a float
		value for threshold.
	:type scoring_configs: list(tuple(int, float))
	:param name: Embedding type name.
	:type param: str
	"""
	K = max(c[0] for c in scoring_configs)

	# Building full search index with single and multi word LU vectors
	inf_vecs = []
	inf_words = []

	for _, row in alignment.l2_frm.iterrows():
		for lu in row["obj"].lus:
			if lu.clean_name not in l2_emb.word2id:
				vec = l2_emb.infer_vector(lu.clean_name)
				if vec is not None:
					inf_vecs.append(vec)
					inf_words.append(lu.clean_name)

	if len(inf_vecs) > 0:
		idx_words = list(l2_emb.word2id.keys())
		idx_words.extend(inf_words)

		search_idx = SearchIndex(
			np.concatenate((l2_emb.embeddings, inf_vecs), axis=0),
			idx_words,
			l2_emb.dim,
		)
	else: 
		search_idx = SearchIndex(
			l2_emb.embeddings,
			list(l2_emb.word2id.keys()),
			l2_emb.dim,
		)

	# Including NN in l2 space of english LUs
	lu_nn = {}

	for _, row in alignment.l2_frm.iterrows():
		for lu in row["obj"].lus:
			if lu.clean_name in search_idx.word2id:
				lu_nn[lu.name] = [(1, search_idx.word2id[lu.clean_name])]

	for _, row in alignment.en_frm.iterrows():
		for lu in row["obj"].lus:
			vec = en_emb.infer_vector(lu.clean_name)
			if vec is not None:
				lu_nn[lu.name] = list(zip(*search_idx.get_knn(vec, K=K)))

	alignment.resources['lu_vec_nn'] = lu_nn
	alignment.resources['id2word'] = {int(i):search_idx.id2word[i] for k,v in lu_nn.items() for d, i in v}

	if len(scoring_configs) == 1:
		scores = lu_scores(alignment, lu_nn, scoring_configs[0][0], scoring_configs[0][1])
		alignment.add_scores(f'lu_{name}', f'lu_{name}', scores, desc='LU translations using MUSE')
	else:
		for c in scoring_configs:
			scores = lu_scores(alignment, lu_nn, c[0], c[1])
			alignment.add_scores(
				f'lu_{name}_{c[0]}_{c[1]}', f'lu_{name}', scores,
				desc=f'LU translations using MUSE (K={c[0]}, Threshold={c[1]})',
				K=c[0], threshold=c[1])


def lu_mean_matching(alignment, en_emb, l2_emb):
	"""Computes scores of each pair of frames on the alignment based on
	multilingual fastText vectors aligned using Multilingual Unsupervised or
	Supervised word Embeddings (MUSE).

	This methods scores the alignment between two frames based on the cosine
	similarity of the mean vectors of all LUs in each frame.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:param en_emb: An :class:`Embedding`instance for english.
	:type en_emb: :class:`Embedding`
	:param l2_emb: An :class:`Embedding`instance for l2.
	:type l2_emb: :class:`Embedding`
	"""
	frm_mean_vecs = {}

	for _, row in alignment.frm.iterrows():
		frm = row["obj"]
		emb = en_emb if frm.lang == "en" else l2_emb
		lu_vecs = (emb.infer_vector(lu.clean_name) for lu in frm.lus)
		lu_vecs = [v for v in lu_vecs if v is not None]
		if len(lu_vecs) > 0:
			frm_mean_vecs[frm.gid] = np.mean(lu_vecs, axis=0)

	# Scoring
	scores = []
	for frame, other in alignment.pairs():
		if frame.gid in frm_mean_vecs and other.gid in frm_mean_vecs:
			scores.append(cosine_sim(frm_mean_vecs[frame.gid], frm_mean_vecs[other.gid]))
		else:
			scores.append(0)

	alignment.add_scores('lu_mean_muse', 'lu_mean_muse', scores, desc='LU centroid similarity using MUSE')


def fe_exact_matching(alignment, en_emb, l2_emb):
	"""Computes scores of each pair of frames on the alignment based on
	multilingual fastText vectors aligned using Multilingual Unsupervised or
	Supervised word Embeddings (MUSE).

	This methods scores the alignment between two frames based on the exact match
	of FE names weighted by the cosine similarity of the same FE's definitions.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:param en_emb: An :class:`Embedding`instance for english.
	:type en_emb: :class:`Embedding`
	:param l2_emb: An :class:`Embedding`instance for l2.
	:type l2_emb: :class:`Embedding`
	"""
	set_fe_vecs(alignment, en_emb, l2_emb)
	def_vecs = alignment.resources["fe_def_vecs"]

	scores = [
		exact_fe_score(frame, other, def_vecs)
		for frame, other in alignment.pairs()
	]

	alignment.add_scores(
		'muse_exact_fe_match', 'muse_fe_matching', scores,
		desc=f'Matching core FE weighted by definition MUSE similarities')


def fe_matching(alignment, en_emb, l2_emb):
	"""Computes scores of each pair of frames on the alignment based on
	multilingual fastText vectors aligned using Multilingual Unsupervised or
	Supervised word Embeddings (MUSE).

	This methods scores the alignment between two frames based on the average
	similarity of FE names weighted by the cosine similarity of the same FE's
	definitions.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:param en_emb: An :class:`Embedding`instance for english.
	:type en_emb: :class:`Embedding`
	:param l2_emb: An :class:`Embedding`instance for l2.
	:type l2_emb: :class:`Embedding`
	"""
	set_fe_vecs(alignment, en_emb, l2_emb, name_vecs=True)
	def_vecs = alignment.resources["fe_def_vecs"]
	name_vecs = alignment.resources["fe_name_vecs"]

	scores = [
		fe_score(frame, other, def_vecs, name_vecs)
		for frame, other in alignment.pairs()
	]

	alignment.add_scores(
		'muse_fe_match', 'muse_fe_matching', scores,
		desc=f'Average core FE name and definition MUSE similarities')


def fe_mixed_matching(alignment):
	"""Merges the scores of the ``muse_fe_match`` and ``muse_exact_fe_match``
	techniques into a new score using the values from exact matches for FEs in
	english and the average for FEs in l2. This scoring should be used when the
	database has FEs in both languages.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:param en_emb: An :class:`Embedding`instance for english.
	:type en_emb: :class:`Embedding`
	:param l2_emb: An :class:`Embedding`instance for l2.
	:type l2_emb: :class:`Embedding`
	"""
	average = next(s for s in alignment.scores if s["id"] == "muse_fe_match")
	exact = next(s for s in alignment.scores if s["id"] == "muse_exact_fe_match")

	scores = [
		(exact if other.fe_lang == "en" else average)["df"].loc[frame.name, other.name]
		for frame, other in alignment.pairs()
	]

	alignment.add_scores(
		'muse_mixed_fe_match', 'muse_fe_matching', scores,
		desc=f'Mixed core FE scoring w/ MUSE similarities',
		normalize=False)


def def_matching(alignment, en_emb, l2_emb):
	"""Computes scores of each pair of frames on the alignment based on
	multilingual fastText vectors aligned using Multilingual Unsupervised or

	This methods scores the alignment between two frames based on the cosine
	similarity of the mean vectors of all words of the frame definition.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:param en_emb: An :class:`Embedding`instance for english.
	:type en_emb: :class:`Embedding`
	:param l2_emb: An :class:`Embedding`instance for l2.
	:type l2_emb: :class:`Embedding`
	"""
	frm_def_vecs = {}

	for _, row in alignment.frm.iterrows():
		frm = row["obj"]
		emb = en_emb if frm.lang == "en" else l2_emb

		if frm.definition:
			vec = emb.infer_vector(frm.definition, ignore_unk=True)
			if vec is not None:
				frm_def_vecs[frm.gid] = vec

	scores = []
	for frame, other in alignment.pairs():
		if frame.gid in frm_def_vecs and other.gid in frm_def_vecs:
			scores.append(cosine_sim(frm_def_vecs[frame.gid], frm_def_vecs[other.gid]))
		else:
			scores.append(0)

	alignment.add_scores('frame_def_muse', 'frame_def_muse', scores, desc='Frame definition similarity using MUSE')
