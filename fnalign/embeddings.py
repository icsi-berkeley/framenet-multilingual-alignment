import os
import numpy as np
from bert_serving.client import BertClient

class WordEmbedding():
	"""A class that implements some basic functionalities over word embeddings.
	"""

	def __init__(self, lang, dim):
		"""Initializes a new :class:`Embedding` with for language ``lang``.

		:param lang: Language of this embedding.
		:type lang: str
		:param dim: Word vector size (dimension).
		:type dim: int
		"""
		self.lang = lang
		self.dim = dim

		self.embeddings = []
		self.id2word = {}
		self.word2id = {}
		self.index = None

	def get_word_emb(self, word):
		"""Gets embedding for a given ``word``.

		:param word: The word used to find the embedding.
		:type word: str
		:returns: the embedding for ``word``
		:rtype: np.array
		"""
		return self.embeddings[self.word2id[word]]

	def load_from_file(self, path, nmax=None):
		"""Loads vectors from .vec file to memory.

		:param path: Path for the .vec file.
		:type path: str
		:param nmax: Maximum number of vectors to be loaded.
		:type nmax: int
		"""
		with open(path, 'r', encoding='utf-8', newline='\n', errors='ignore') as fp:
			if not nmax:
				nmax, _ = next(fp).split()
				nmax = int(nmax)

			np_vecs = np.empty([nmax, self.dim], dtype=np.float32)

			for i, line in enumerate(fp):
				if i == nmax:
						break

				word, vec = line.rstrip().split(' ', 1)
				np_vecs[i] = np.fromstring(vec, dtype=np.float32, sep=' ')
				self.word2id[word] = i
				self.id2word[i] = word

		# Normalization
		np_vecs = np_vecs / np.linalg.norm(np_vecs, 2, 1)[:, None]
		self.embeddings = np_vecs

	def save_to_file(self, path):
		"""Save embeddings from memory to .vec file.

		:param path: Path for the output .vec file.
		:type path: str
		"""
		with open(path, "w") as fp:
			fp.write(f'{len(self.embeddings)} {self.dim}\n')
			fp.writelines(
				f'{v} {" ".join(str(x) for x in self.embeddings[k])}\n'
				for k,v in self.id2word.items()
			)

	def infer_vector(self):
		"""Abstract method to infer the vector representation of a text."""
		raise NotImplementedError("This method should be implemented by subclasses")


class MuseWordEmbedding(WordEmbedding):
	"""A class that implements some basic functionalities over fastText MUSE word
	embeddings.
	"""

	def infer_vector(self, text, ignore_unk=False):
		"""Infers a vector for ``text``. When its value contains more than one
		token, the string is split and an average of each token embedding is
		returned. When ``ignore_unk`` is True, this function returns the average of
		the known tokens of ``text``, when it is False, if any of the tokens are
		unknown, the function returns None. 

		:param text: String that the vector will be inferred.
		:type text: str
		:param ignore_unk: If unknown tokens should be taken into consideration.
		:type ignore_unk: bool
		:returns: A vector for ``text`` or ``None`` if one of its token is unknown.
		:rtype: np.array
		"""
		word_embs = []
		for word in text.split():
			if word in self.word2id:
				word_embs.append(self.get_word_emb(word))
			elif not ignore_unk:
				return None
		else:
			return np.mean(word_embs, axis=0) if len(word_embs) > 0 else None


class BertWordEmbedding(WordEmbedding):
	"""A class that implements some basic functionalities over BERT word
	embeddings.
	"""

	def __init__(self, lang, dim):
		super().__init__(lang, dim)
		self.bc = None

	def get_client(self):
		"""Instantiates and returns the BERT server client of this instance. The
		instantiated client will be cached for subsequent calls.
		
		:returns: ``class:BertClient`` of this instance.
		:rtype: ``class:BertClient``
		"""
		if self.bc is None:
			self.bc = BertClient()

		return self.bc

	def load_from_vocab(self, words):
		"""Loads vectors from a list of words. When this method is used the vectors
		for each word are first inferred from the remote BERT server.

		:param words: List of words in the vocabulary.
		:type words: list[str]
		"""
		bc = self.get_client()
		np_vecs = bc.encode(words)

		for i, word in enumerate(words):
			self.word2id[word] = i
			self.id2word[i] = word

		# Normalization
		np_vecs = np_vecs / np.linalg.norm(np_vecs, 2, 1)[:, None]
		self.embeddings = np_vecs

	def infer_vector(self, text):
		"""Infers a vector for ``text``.

		:param text: String that the vector will be inferred.
		:type text: str
		:returns: A vector for ``text`` or ``None`` if one of its token is unknown.
		:rtype: np.array
		"""
		bc = self.get_client()
		return bc.encode([text])[0]


class SearchIndex:

	def __init__(self, vecs, words, dim):
		"""Initializes a new :class:`SearchIndex` for vectors ``vecs`` with
		dimension ``dim`` and words ``words``.

		:param vecs: List of vectors.
		:type vecs: list[np.array]
		:param words: String representation of ``vecs``.
		:type words: list[str]
		:param dim: Vector size.
		:type dim: int
		"""
		self.id2word = {}
		self.word2id = {}

		for i, w in enumerate(words):
			self.id2word[i] = w
			self.word2id[w] = i

		import faiss
		index = faiss.IndexFlatIP(dim)
		index.add(np.array(vecs))

		self.index = index


	def get_knn(self, vec, K=5):
		"""Returns the indices of the ``K`` nearest neighbors of ``vec`` in the
		:class:`Embedding` space.
		
		:param vec: The vector to get its neighbors
		:type vec: np.array
		:param K: Number of neighbors to search.
		:type K: int
		:returns: Indices of ``K`` nearest vectors of ``vec```
		:rtype: np.array
		"""
		D, I = self.index.search(vec.reshape(1, -1), K)
		return D[0], I[0]
	