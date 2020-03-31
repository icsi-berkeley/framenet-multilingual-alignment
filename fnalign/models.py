"""This module contains the definition of models for the Multilingual FrameNet
alignment.

.. note::
	Classes that represent FrameNet elements such as :class:`Frame` and
	:class:`LexUnit` should be moved to a global "framenet" package since they
	are useful for every FrameNet project application in Python.

.. moduleauthor:: Arthur Lorenzi Almeida <lorenzi.arthur@gmail.com>
"""

import json
import os
import itertools
import re
from datetime import datetime
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0

class FrameNet:
	"""A class used to represent a FrameNet database.

	This representation of a FrameNet should be used to store a collection of
	frames that come from the same database and the language of that database.
	For some databases that language might reflect only the LU languages.
	"""

	def __init__(self, name, lang, frames):
		self.name = name
		self.lang = lang
		self.frames = frames

		self.detect_langs()

	def detect_langs(self):
		"""Sets languages of all FEs of this FrameNet. This method assumes that all
		FEs of a frame are in the same language and to infer this language uses a
		detection model and the concatenation of all of the FEs description of each
		frame.

		"""
		for frm in self.frames:
			text = ' '.join(fe.definition for fe in frm.fes if fe.definition is not None)

			if text:
				lang = detect(text)
				frm.fe_lang = lang
				for fe in frm.fes:
					fe.lang = lang


class Frame:
	"""A class used to represent a Frame.

	This is a simplified representation of a frame containing only a small set of
	attributes required for the frame aligment between two different databases.
	"""

	def __init__(self, id, name, name_en, db_name, lang, definition=None):
		"""Initializes a :class:`Frame` object.

		:param id: Frame id on its framenet database.
		:type id: str
		:param name: Frame name.
		:type name: str
		:param name_en: The english name for l2 frames.
		:type name_en: str
		:param db_name: The database/XML schema name.
		:type db_name: str
		:param lang: Frame's source database language identifier.
		:type lang: str
		:param definition: Frame definition
		:type definition: str
		"""
		self.id = id
		self.gid = f'{id}.{lang}'
		self.name = name
		self.name_en = name_en
		self.definition = definition
		self.db_name = db_name
		self.lang = lang

		self.lus = set()
		self.fes = set()
		self.fe_lang = None
	
	def core_fes(self):
		"""Yields all core FEs of the frame.

		:returns: An iterator over the core FEs of this frame.
		:rtype: Iterator[:class:`FrameElement`]
		"""
		for fe in self.fes:
			if fe.type.lower() == "core":
				yield fe

	def __str__(self):
		return f'Frame(\'{self.name}.{self.lang}\')'


class LexUnit:
	"""A class used to represent a lexical unit.

	This is a simplified representation of a lexical unit containing only a small
	set of attributes required for the frame aligment between two different
	databases.
	"""

	def __init__(self, _id, name, pos):
		"""Initializes a :class:`LexUnit` object assigning its id, name, POS tag and 
		the preprocessed name.
		"""
		self.id = _id
		self.name = name
		self.pos = pos.lower()

		clean_name = name[:-1-len(pos)].lower()
		clean_name = re.sub(r"[\(\)\[\]]", "", clean_name)
		clean_name = clean_name.replace("-", " ")
		self.clean_name = clean_name

	def __str__(self):
		return f'LexUnit(\'{self.name}.{self.pos}\')'


class FrameElement:
	""" A class used to represent a frame element.

	This is a simplified representation of a frame element that contains only a
	set of attributes that are used for the multilingual alignment.
	"""
	def __init__(self, _id, name, name_en, etype, abbrev=None, definition=None):
		"""Initializes a :class:`FrameElement` object assigning its id, name,
		english name, type, name abbreviation and definition.
		"""
		self.id = _id
		self.name = name
		self.name_en = name_en
		self.type = etype
		self.abbrev = abbrev
		self.lang = None

		if definition and definition.strip():
			self.definition = definition.strip()
		else:
			self.definition = None

	def __str__(self):
		return f'FrameElement(\'${self.name}\')'


class CustomEncoder(json.JSONEncoder):
	"""A custom JSON encoder to be used when serializing :class:`Alignment`
	instances to JSON. It adds support to :class:`numpy.ndarray` and :class:`set`
	serialization.
	"""

	def default(self, obj):
		if isinstance(obj, np.float32):
			return float(obj)
		if isinstance(obj, np.int64):
			return int(obj)
		if isinstance(obj, set):
			return list(obj)
		elif isinstance(obj, np.ndarray):
			return obj.tolist()
		else:
			return json.JSONEncoder.default(self, obj)


class Alignment():
	"""A class to represent an Alignment between Berkeley FrameNet (BFN) and a
	different FrameNet database. BFN's language is english, called "en" in this
	class context, while the other database language is called "l2" throughout
	the code.

	This class is used to store alignment data in a convenient format and provide
	an useful API to alignment tasks. This API should provide implementations of
	common operations when aligning FrameNets - such as iteration over pair of
	frames - and allow access to data generated by other alignment procedure/
	techniques.
	"""

	def __init__(self, en_fn, l2_fn):
		"""Initializes an :class:`Alignment` object.

		:param en_fn: :class:`FrameNet` instance for english.
		:type en_fn: :class:`FrameNet`
		:param l2_fn: :class:`FrameNet` instance for L2.
		:type l2_fn: :class:`FrameNet`
		"""
		self.version = 1
		self.scores = []
		self.resources = {}

		self.en_fn = en_fn
		self.l2_fn = l2_fn

		self.load()


	def __get_indices(self):
		"""Gets frame indices in a format appropriate for serialization.

		:returns: List of frame indices.
		:rtype: list[list[str]].
		"""
		return [list(self.en_frm.index), list(self.l2_frm.index)]


	def __get_frames(self):
		"""Gets a frame global id mapping to frame data object.

		:returns: A dictionary of frame global ids and their respective frames.
		:rtype: dict.
		"""
		return {
			frame.gid: {
				"gid": frame.gid,
				"name": frame.name,
				"language": frame.lang,
				"LUs": [l.name for l in frame.lus],
				"FEs": [
					{
						"name": f.name,
						"name_en": f.name_en,
					} for f in frame.fes if f.type == "Core"
				]
			}
			for frame in self.frm["obj"]
		}

	def __get_alignments(self, ignore_scores=set()):
		"""Gets list of alignment scores of different techniques for serialization.

		:param ignore_scores: set of alignment types to not dump scores.
		:type ignore_scores: set
		:returns: A list of dictionaries contaning score's type and values.
		:rtype: list[dict].
		"""
		alignments = []

		for score_obj in self.scores:
			copy = score_obj.copy()
			if score_obj['type'] not in ignore_scores:
				copy["data"] = copy["df"].values
			del copy["df"]
			alignments.append(copy)

		return alignments


	def load(self):
		"""Loads this object with frame data.

		:returns: self.
		"""
		en_frm = pd.DataFrame(self.en_fn.frames, columns=['obj'])
		l2_frm = pd.DataFrame(self.l2_fn.frames, columns=['obj'])

		self.frm = pd.concat([en_frm, l2_frm])
		self.frm = self.frm.set_index(self.frm["obj"].apply(lambda x: x.gid))
		self.frm['name'] = self.frm['obj'].apply(lambda x: x.name)
		self.frm['lang'] = self.frm['obj'].apply(lambda x: x.lang)

		self.en_frm = self.frm[self.frm['lang'] == 'en']
		self.l2_frm = self.frm[self.frm['lang'] != 'en']

		return self


	def pairs(self):
		"""Yields all possible pairs of frames betweem english and l2. The first
		frame is always from BFN.

		:returns: An iterator over frame pairs
		:rtype: Iterator[(:class:`Frame`, :class:`Frame`)]
		"""
		for x, y in itertools.product(self.en_frm['obj'], self.l2_frm['obj']):
			yield x, y


	def add_scores(self, aid, atype, data, **kwargs):
		"""Adds a score matrix to this object data. The matrix should be inputed
		as a list of scores for each possible alignment pair, i.e., its length must
		be the same as the number of pairs yielded by :func:`pairs`.

		:param aid: An unique identifier for the aligment score.
		:type aid: str
		:param atype: The aligment type identifier referencing the technique used.
		:type atype: str
		:param data: A score list with the same len as yielded by :func:`pairs`.
		:type data: list[float]
		:param desc: A small sentence to describe the techinque used to score.
		:type desc: str
		:param K: The K value used for nearest neighbors search used.
		:type K: int
		:param threshold: The LU distance threshold used to determine matches
		:type threshold: float
		"""
		# if "normalize" not in kwargs or kwargs["normalize"]:
		# 	indices = [i for i, s in enumerate(data) if s > 0]
		# 	norm = rankdata([data[i] for i in indices], "max") / len(indices)

		# 	for i, s in zip(indices, norm):
		# 		data[i] = s

		self.scores.append({
			"id": aid,
			"type": atype,
			"df": pd.DataFrame(
				np.array(data).reshape(len(self.en_frm), len(self.l2_frm)),
				index=self.en_frm['name'],
				columns=self.l2_frm['name'],
			),
			**kwargs
		})


	def dump(self, ignore_scores=set()):
		"""Serializes this object's data to JSON and saves it as a new file. All 
		files are dumped to the "out" folder.

		:param ignore_scores: set of alignment types to not dump scores.
		:type ignore_scores: set
		"""
		timestamp = datetime.now().strftime("%Y%m%d%H%M")
		path = os.path.join('out', f'{timestamp}_{self.l2_fn.name}.json')

		try:
			os.makedirs("out")
		except FileExistsError:
			pass

		with open(path, 'w+') as fp:
			json.dump({
				"version": self.version,
				"db": (self.en_fn.name, self.l2_fn.name),
				"lang": (self.en_fn.lang, self.l2_fn.lang),
				"indices": self.__get_indices(),
				"frames": self.__get_frames(),
				"alignments": self.__get_alignments(ignore_scores=ignore_scores),
				"resources": self.resources,
			}, fp, cls=CustomEncoder)

