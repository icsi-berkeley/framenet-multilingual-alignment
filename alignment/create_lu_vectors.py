import os
import re
import json
import itertools
from collections import defaultdict
import numpy as np
from bert_serving.client import BertClient
from fnalign.loaders import load
from bertalign.tokenization import load_vocab, BasicTokenizer, WordpieceTokenizer

MODEL_PATH = "/home/arthur/Projects/framenet-multilingual-alignment/models/50k_multi_aligned_cased_L-12_H-768_A-12"

def chunks(lst, n):
	"""Yield successive n-sized chunks from lst."""
	for i in range(0, len(lst), n):
		yield lst[i:i + n]

def bert_lu_annotation_embeddings(fn):
	vocab = load_vocab(os.path.join(MODEL_PATH, "vocab.txt"))
	basic_tokenizer = BasicTokenizer(do_lower_case=False)
	wordpiece_tokenizer = WordpieceTokenizer(vocab=vocab)
	regex = re.compile(r'([ :]{4,}| \.\.\. )')

	sentences = []

	for frame in fn.frames:
		for lu in frame.lus:
			if len(lu.anno_sents) == 0:
				tokens = wordpiece_tokenizer.tokenize(lu.clean_name)
				
				if '[UNK]' not in tokens:
					sentences.append({
						"tokens": tokens,
						"lu_pos": len(tokens) - 1,
						"lu_id": lu.id,
					})

			for anno in lu.anno_sents:
				sentence = anno["sentence"]
				start = max(anno["lu_pos"][0]-1, 0)
				end = min(anno["lu_pos"][1]+1, len(sentence))

				a = basic_tokenizer.tokenize(re.sub(regex, ' ', sentence[:start]))
				w = basic_tokenizer.tokenize(sentence[start:end])
				b = basic_tokenizer.tokenize(re.sub(regex, ' ', sentence[end:]))

				tokenized = [wordpiece_tokenizer.tokenize(t) for t in a+w+b]
				shift = list(itertools.accumulate([len(t) for t in tokenized]))

				tokens = [s for subtokens in tokenized for s in subtokens]
				pos = shift[len(a)+len(w)-1]-1

				if tokens[pos] != '[UNK]':
					sentences.append({
						"tokens": tokens,
						"lu_pos": pos,
						"lu_id": lu.id
					})

	# sentences = sentences[:100]

	vecs = None
	bc = BertClient()

	for chunk in chunks(sentences, 1024):
		tokens = [s["tokens"] for s in chunk]
		res = bc.encode(tokens, is_tokenized=True)
		sel = res[np.arange(len(res)), [s["lu_pos"] + 1 for s in chunk]]

		if vecs is not None:
			vecs = np.concatenate((vecs, sel), axis=0)
		else: 
			vecs = sel

	vecs = vecs.reshape((len(sentences), 768))

	embs = defaultdict(list)
	for lu, vec in zip(sentences, vecs):
		embs[lu["lu_id"]].append(vec)

	return embs


def write_lu_vecs(embs_by_lu, filename):
	path = os.path.join('data', 'bert', filename)
	with open(path, 'w') as fp:
		json.dump({
			k: np.mean(v, axis=0).tolist()
			for k, v in embs_by_lu.items()
		}, fp)


if __name__ == "__main__":
	configs = [
		('bfn', 'en'),
		('fnbrasil', 'pt'),
	]

	for db_name, lang in configs:
		fn = load(db_name, lang)
		embs_by_lu = bert_lu_annotation_embeddings(fn)
		write_lu_vecs(embs_by_lu, f'{db_name}_lu_embs.json')