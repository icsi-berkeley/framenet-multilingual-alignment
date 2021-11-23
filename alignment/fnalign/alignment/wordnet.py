"""This module contains a collection of alignment algorithms that are based on
Open Multilingual Wordnet.

.. moduleauthor:: Arthur Lorenzi Almeida <lorenzi.arthur@gmail.com>
"""

import re
import itertools
from collections import defaultdict
import numpy as np
import pandas as pd
from nltk.corpus import wordnet as wn

FN_WN_POS_MAP = {
	"a": "a",
	"v": "v",
	"n": "n",
	"adv": "r",
}

LANG_MAP = {
	"en": "eng",
	"es": "spa",
	"fr": "fra",
	"ja": "jpn",
	"pt": "por",
	"zh": "cmn",
	"sv": "swe",
	"nl": "nld",
	"de": "deu",
}


def get_mappings(frm_df):
	"""Gets commonly used mappings, namely:
	
	* LU to Synset
	* Synset to LU
	* Frame to Synset

	:param frm_df: A frame DataFrame.
	:type frm_df: pandas.DataFrame
	:returns: Dictionary containing mappings.
	:rtype: dict[str, defaultdict(set)]
	"""
	lu_to_syn = defaultdict(set)
	syn_to_lu = defaultdict(set)
	frm_to_syn = defaultdict(set)

	for _, row in frm_df.iterrows():
		frame = row['obj']

		for lu in frame.lus:
			lemma = re.sub(r'\s?[^\w&\s&\-].*', '', lu.name)
			pos = FN_WN_POS_MAP[lu.pos] if lu.pos in FN_WN_POS_MAP else None

			try:
				for syn in wn.synsets(lemma, lang=LANG_MAP[frame.lang], pos=pos):
					lu_to_syn[lu.gid].add(syn.name())
					syn_to_lu[syn.name()].add(lu.name)
					frm_to_syn[frame.gid].add(syn.name())
			except:
				print(f"Error searching for lemma synsets. Lemma={lemma}, POS={lu.pos}")

	return { 
		"lu_to_syn": lu_to_syn,
		"syn_to_lu": syn_to_lu,
		"frm_to_syn": frm_to_syn,
	}


def get_synsets(alignment):
	"""Gets synsets definitions and lemmas for english and ``alignment.lang``.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:returns: Dictionary containing synset data.
	:rtype: dict[str, dict]
	"""
	synset_objs = [
		wn.synset(s)
		for s in alignment.resources['syn_to_lu'].keys()
	]

	return {
		syn.name(): {
			"definition": syn.definition(),
			**{
				lang: sorted([l.name() for l in syn.lemmas(lang=LANG_MAP[lang])])
				for lang in ['en', alignment.l2_fn.lang]
			}
		}
		for syn in synset_objs
	}


def set_resources(alignment):
	r"""Includes wordnet resources in ``alignment`` data if they doesn't exist
	yet.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	"""
	if 'lu_to_syn' not in alignment.resources:
		alignment.resources.update(get_mappings(alignment.frm))
		alignment.resources['syn_data'] = get_synsets(alignment)


def synset_matching(alignment):
	r"""Computes scores between each pair of frames on the alignment based on
	synsets associated to the frames.
	
	A frame is associated to a synset if the form of one of its LUs is a lemma
	beloging to the synset. Once every frame is associated to a set of synsets,
	the following scores are computed for each pair *<x,y>*:

	* *s*\ :sub:`x,y` =  \|*Syn*\ :sub:`x` ∩ *Syn*\ :sub:`y`  \| ÷  \|*Syn*\ :sub:`x`  \|
	* *s*\ :sub:`x,y` =  \|*Syn*\ :sub:`x` ∩ *Syn*\ :sub:`y`  \| ÷  \|*Syn*\ :sub:`y`  \|

	Where *Syn*\ :sub:`x` is the set of synsets associated to frame *x*.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	"""
	set_resources(alignment)
	syn = alignment.resources["frm_to_syn"]

	scores = []
	scores_inv = []
	for frame, other in alignment.pairs():
		if len(syn[frame.gid]) == 0 or len(syn[other.gid]) == 0:
			scores.append(0)
			scores_inv.append(0)
			continue

		inter_len = len(syn[frame.gid] & syn[other.gid])
		scores.append(inter_len/len(syn[frame.gid]))
		scores_inv.append(inter_len/len(syn[other.gid]))

	alignment.add_scores(
		'synset', 'synset', scores,
		desc=f'Synset count {alignment.en_fn.lang}→{alignment.l2_fn.lang}')
	alignment.add_scores(
		'synset_inv', 'synset_inv', scores_inv,
		desc=f'Synset count {alignment.l2_fn.lang}→{alignment.en_fn.lang}')


def lu_matching(alignment):
	r"""Computes scores between each pair of frames on the alignment based on the
	matching of LUs through synsets.

	For each pair of frames *<x,y>*, the algorithm computes *LU*\ :sub:`x` and
	*LU*\ :sub:`y`, the LU sets of *x* and *y* respectively. Let *L = LU*\
	:sub:`x` *∪* LU\ :sub:`y` . Then, for each *i* in *L*, the algorithm computes
	the set of synsets *S*\ :sub:`i` where *i* is one of its lemmas. Let *S* be
	the union of all *S*\ :sub:`i` for all *i ∈ L*. In order to calculate the
	score, the graph *G=(V,E)* is defined for *V = L ∪ S* and *E* = {*<i, j>* for
	each *i ∈ L*, for each *j ∈ S*\ :sub:`i` }. Finally, *Match*\ :sub:`x` is
	computed as the set of *i ∈ LU*\ :sub:`x` such that a path from *i* to any *m
	∈ LU*\ :sub:`y` exists. The score value is defined as follows:

	* *s*\ :sub:`x,y` =  \|*Match*\ :sub:`x`  \| ÷  \|*LU*\ :sub:`x`  \|

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	"""
	set_resources(alignment)
	lu_to_syn = alignment.resources["lu_to_syn"]

	scores = []
	for frame, other in alignment.pairs():
		if len(frame.lus) == 0:
			scores.append(0)
			continue

		count = 0
		for lu1 in frame.lus:
			for lu2 in other.lus:
				if lu_to_syn[lu1.gid] & lu_to_syn[lu2.gid]:
					count += 1
					break

		scores.append(count/len(frame.lus))

	alignment.add_scores(
		'lu_wordnet', 'lu_wordnet', scores,
		desc=f'LU translations using WordNet {alignment.en_fn.lang}→{alignment.l2_fn.lang}')
