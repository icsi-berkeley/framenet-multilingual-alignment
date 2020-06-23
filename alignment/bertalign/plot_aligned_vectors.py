import os
import itertools
import random
from collections import defaultdict
import numpy as np
from bert_serving.client import BertClient

import tokenization
from create_alignment_data import get_sample

def load_aligned_words(string):
	string = string.replace('\n', '')

	return [
		tuple(map(int, pair.split('-')))
		for pair in string.split(' ')
	]


def pair_counts(lines, maps):
	counts = defaultdict(lambda: defaultdict(lambda: 1))

	for l, m in zip(lines, maps):
		if l.strip() and m.strip():
			a, b = l.split(" ||| ")
			
			tokens_a = a.split()
			tokens_b = b.split()
			align = load_aligned_words(m)

			for a in align:
				counts[tokens_a[a[0]]][tokens_b[a[1]]] += 1

	return counts


def most_frequent_pairs(counts):
	counts_list = [
		([k1, k2], v)
		for k1, o2 in counts.items()
		for k2, v in o2.items()
	]
	counts_list.sort(key=lambda x: -x[1])

	return counts_list


def get_inputs(words_a, words_b, pair, tokenizer):
	tokenized_a = [tokenizer.tokenize(t) for t in words_a]
	tokenized_b = [tokenizer.tokenize(t) for t in words_b]

	cum_a = list(itertools.accumulate([len(t) for t in tokenized_a]))
	cum_b = list(itertools.accumulate([len(t) for t in tokenized_b]))

	pos = (cum_a[words_a.index(pair[0])]-1, cum_b[words_b.index(pair[1])]-1)

	return {
		"a": [s for t in tokenized_a for s in t],
		"b": [s for t in tokenized_b for s in t],
		"pos": pos,
	}



def get_sentences(lines, pairs, tokenizer, k=5):
	sents = list()

	for i, p in enumerate(pairs):
		sents.append(list())

		for l in lines:
			a, b = l.split(" ||| ")

			tokens_a = a.split()
			tokens_b = b.split()

			if p[0] in tokens_a and p[1] in tokens_b:
				sents[i].append(get_inputs(tokens_a, tokens_b, p, tokenizer))

			if len(sents[i]) == k:
				break

	return sents


def get_embeddings(sentences):
	bc = BertClient()
	flat = [
		v
		for pair_sents in sentences
		for sent_info in pair_sents
		for k,v in sent_info.items()
		if k == "a" or k == "b"
	]
	positions = [
		p + 1 # [CLS]
		for pair_sents in sentences
		for sent_info in pair_sents
		for p in sent_info["pos"]
	]

	# bert-serving-start -show_tokens_to_client -pooling_layer -1 -pooling_strategy NONE -max_seq_len 256 -max_batch_size 128 -model_dir models/50k_multi_aligned_cased_L-12_H-768_A-12
	res, _ = bc.encode(flat, show_tokens=True, is_tokenized=True)
	sel = res[np.arange(len(res)), positions]
	
	return sel.reshape((len(sentences), -1, 2, sel.shape[-1]))


sent_path = os.path.join("data", "europarl", "es-en", "fastalign-europarl.es-en")
sent_fp = open(sent_path, 'r')
lines = sent_fp.read().splitlines()

map_path = os.path.join("data", "europarl", "es-en", "fastalign-europarl.es-en.intersect.align")
# map_fp = open(map_path, 'r')
# maps = map_fp.read().splitlines()

# counts = pair_counts(lines, maps)
# most_frequent_pairs(counts)

pairs = [
	('year', 'año'),
	('wanted', 'quería'),
	('question', 'cuestión'),
	('I', 'yo'),
	('opportunity', 'oportunidad'),
	('problem', 'problema'),
	('love', 'amor'),
]
K = 10

tokenizer = tokenization.WordpieceTokenizer(
		vocab=tokenization.load_vocab("/home/arthur/Projects/bert/models/multi_aligned_cased_L-12_H-768_A-12/vocab.txt"))

rng = random.Random(1234)
sample = set(get_sample(sent_path, map_path, rng, 50000))
lines = [
	l for i,l in enumerate(lines)
	if i in sample
]

sents = get_sentences(lines, pairs, tokenizer, k=K)
embs = get_embeddings(sents)

from sklearn.manifold import TSNE
X = embs.reshape((-1, embs.shape[-1]))
X_embedded = TSNE(n_components=2, perplexity=20, metric='cosine').fit_transform(X)
X_embedded.shape

import matplotlib.pyplot as plt
markers = ["o", "v", "x", "s", "^", ">", "<"]
data_ranges = list(range(0, len(X_embedded), K * 2)) + [len(X_embedded)]

for i in range(len(pairs)):
	data = X_embedded[data_ranges[i]:data_ranges[i+1], :]
	# plot english
	en = data[::2]
	plt.scatter(en[:,0], en[:,1], c='blue', label=pairs[i][0], marker=markers[i])
	# plot L2
	l2 = data[1::2]
	plt.scatter(l2[:,0], l2[:,1], c='red', label=pairs[i][1], marker=markers[i])

plt.legend(bbox_to_anchor=(1.04, 0.5), loc='center left')
plt.subplots_adjust(right=0.7)
plt.savefig('contextual_word_graph.png')


