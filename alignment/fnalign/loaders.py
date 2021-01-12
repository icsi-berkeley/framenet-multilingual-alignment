"""This subpackage contains the definition of classes specialized in reading
FrameNet databases from .xml files in various schemas. The utility function
:func:`load` is provided as an interface to automatically detect the correct
loader and use it.

.. note::
	All loader classes must inherit from :class:`FNLoader`.

.. note::
	Ideally, this module's functionality should be in a "framenet" global package
	because it may be useful in different projects.

.. moduleauthor:: Arthur Lorenzi Almeida <lorenzi.arthur@gmail.com>

"""

import os
import re
import logging
import pandas as pd
import xml.etree.ElementTree as ET

from fnalign.models import FrameNet, Frame, LexUnit, FrameElement

SWEFN_FE_TYPES = {
	"coreElement": "Core",
	"peripheralElement": "Peripheral",
}

NS = '{http://framenet.icsi.berkeley.edu}'

class FNLoader():
	"""A class used to represent a FrameNet XML loader.

	Each loader is instantiated for a specific database schema that is stored in
	``db_name``.
	"""

	def __init__(self, db_name):
		self.db_name = db_name
		self.base_path = os.path.join("data", self.db_name)

	@staticmethod
	def supported_db():
		"""A static method that returns the database schemas supported by this
		class. This method should always be overriden by subclasses.

		:returns: List of supported database schemas.
		:rtype: list[str]
		"""
		return ['bfn', 'frenchfn', 'japanesefn', 'spanishfn']

	def frames(self):
		"""Yields the xml root of all existent frames on the dataset identified by
		``self.db_name``.

		:returns: An iterator over :class:`xml.etree.ElementTree.Element`.
		:rtype: Iterator[xml.etree.ElementTree.Element]
		"""
		path = os.path.join(self.base_path, 'frame')
		files = [os.path.join(path, p) for p in os.listdir(path) if p.endswith(".xml")]

		for filename in files:
			yield ET.parse(filename).getroot()

	def parse_def(self, root):
		"""Parses a frame or FE definition to XML and removes the examples section.
		This method assumes that the definition is a XML string, if parsing fails
		None is returned.

		:param root: The definition XML element.
		:type root: xml.etree.ElementTree.Element
		:returns: The definition string.
		:rtype: str
		"""
		try :
			def_root = ET.fromstring(root.text)
			def_str = def_root.text if def_root.text is not None else ""
			for child in def_root:
				if child.tag == "ex":
					break
				if child.text is not None:
					def_str += child.text
				if child.tail is not None:
					def_str += child.tail

			return def_str
		except:
			return None

	def parse_frame(self, root):
		"""Extracts from ``root`` the necessary data to instantiate a
		:class:`Frame` object. This method should be overriden when a schema uses
		different attribute names for the id, name and english frame or this data
		is not on attributes.

		:param root: The frame's XML root tag.
		:param type: xml.etree.ElementTree.Element
		:returns: The frame id, name and english name
		:rtype: (str, str, str)
		"""
		name = root.get("name")
		definition = self.parse_def(root.find(f"{NS}definition"))
		return root.get("ID"), name, name, definition
	
	def parse_lus(self, root):
		"""Yields all lexical units under ``root``. This method should be overriden
		when a schema uses different tags, attributes or the lexical units are in a
		different place of ``root``'s tree.

		:param root: The frame's XML root tag.
		:param type: xml.etree.ElementTree.Element
		:returns: An iterator over lexical units id, name, POS tag, annotated sentences.
		:rtype: Iterator[(str, str, str, str)]
		"""
		for el in root.findall(f"{NS}lexUnit"):
			path = os.path.join(self.base_path, 'lu', f'lu{el.get("ID")}.xml')

			try:
				lu_root = ET.parse(path).getroot()
				annotations = list()

				for anno_set in lu_root.findall(f"{NS}subCorpus/{NS}sentence"):
					text_el = anno_set.find(f'{NS}text')
					sentence = text_el.text if text_el else anno_set.text
					target = anno_set.find(f'{NS}annotationSet/{NS}layer[@name="Target"]/{NS}label[@name="Target"]')

					if target is not None:
						annotations.append({
							"sentence": sentence,
							"lu_pos": (int(target.get("start")), int(target.get("end"))+1)
						})

				yield el.get("ID"), el.get("name"), el.get("POS"), annotations
			except FileNotFoundError:
				yield el.get("ID"), el.get("name"), el.get("POS"), list()


	def parse_fes(self, root):
		"""Yields all frame elements under ``root``. This method should be
		overriden when a schema uses different tags, attributes or the definition
		is not in a XML format.

		:param root: The frame's XML root tag.
		:param type: xml.etree.ElementTree.Element
		:returns: An iterator over frame element id, name, english name, type and
			abbreviation.
		:rtype: Iterator[(str, str, str)]
		"""
		for el in root.findall(f"{NS}FE"):
			def_str = self.parse_def(el.find(f"{NS}definition"))
			yield (el.get("ID"), el.get("name"), el.get("name"), el.get("coreType"),
				el.get("abbrev"), def_str)

	def load(self, lang='en'):
		"""Loads all frames and their LUs from XML files and returns a frame list.
		This methods acts as an orchestrator for the loading process, that's why it
		list directory contents and parses the XML files, but always delegate the
		responsibility of finding frame and LU data to :func:`__parse_frame` and
		:func:`__parse_lus`, respectively.
		It also assumes that all XML files are located inside a folder with the
		same name as the ``db_name`` attribute and that this folder is inside the
		"data" folder.

		>>> loader = FNLoader("chinesefn")
		>>> loader.load("cmn") # Will look for files inside "data/chinesefn"
		[Frame('Differentiation.cmn'), ...]

		:param lang: Language identifier to be attributed to loaded frames.
		:type lang: str
		:returns: List of frame objects.
		:rtype: list[:class:`Frame`]
		"""
		frames = []

		for root in self.frames():
			_id, name, name_en, definition = self.parse_frame(root)
			frame = Frame(_id, name, name_en, self.db_name, lang, definition=definition)

			frame.lus = set(
				LexUnit(_id, f'{frame.gid}.{_id}', name, pos, annotations)
				for _id, name, pos, annotations in self.parse_lus(root)
			)

			frame.fes = set(
				FrameElement(_id, name, name_en, etype, abbrev, definition)
				for _id, name, name_en, etype, abbrev, definition in self.parse_fes(root)
			)

			frames.append(frame)

		return FrameNet(self.db_name, lang, frames)


class ChineseFNLoader(FNLoader):

	@staticmethod
	def supported_db():
		return ['chinesefn']

	def __init__(self, db_name):
		super().__init__(db_name)
		self.id = 0

	def parse_frame(self, root):
		info = root.find("Frame_Info")
		self.id += 1
		return self.id, info.get("frame_name"), info.get("frame_name_en"), info.get("frame_def")
	
	def parse_lus(self, root):
		info = root.find("Frame_Info").find("LexicalUnit_Info")
		for el in info.findall("lexicalunit"):
			self.id += 1
			yield self.id, el.get("lexicalunit_name"), el.get("lexicalunit_pos_mark"), []

	def parse_fes(self, root):
		info = root.find("Frame_Info").find("FrameElement_Info")
		for el in info.findall("FE"):
			self.id += 1
			yield (self.id, el.get("frameelement_name"), el.get("frameelement_name_en"),
				None, el.get("frameelement_abbr"), None)


class FNBrasilLoader(FNLoader):

	@staticmethod
	def supported_db():
		return ['fnbrasil', 'fncopa', 'salsa']

	def __init__(self, db_name):
		super().__init__(db_name)
		self.def_ex_re = re.compile(r'^Ex:(.|\n)*', re.MULTILINE)
		self.def_com_re = re.compile(r'^s\d+:.*$', re.MULTILINE)

	def clean_def(self, definition):
		"""Returns the frame/FE definition text with no example sentences or
		annotation commentaries.

		:param definition: The raw text of the FE definition.
		:type definition: str
		:returns: The clean text of the FE definition.
		:rtype: str
		"""
		if definition:
			new = self.def_ex_re.sub("", definition)
			new = self.def_com_re.sub("", new)
			new = new.strip()
			return new if re.match(r'\w', new) else None
		else :
			return None

	def frames(self):
		filename = os.path.join("data", self.db_name, "data.xml")
		root = ET.parse(filename).getroot()

		for frm_node in root.findall("frame"):
			yield frm_node

	def parse_frame(self, root):
		definition = self.clean_def(root.find("definition").text)
		return root.get("ID"), root.get("name"), None, definition

	def parse_lus(self, root):
		for el in root.find("lexunits").findall("lexunit"):
			path = os.path.join(self.base_path, 'lu', f'lu{el.get("ID")}.xml')

			try:
				lu_root = ET.parse(path).getroot()
				annotations = list()

				for anno_set in lu_root.findall(f"subcorpus/annotationSet"):
					sentence = anno_set.find(f'sentence/text').text
					target = anno_set.find(f'layers/layer[@name="Target"]/labels/label[@name="Target"]')

					if target is not None:
						annotations.append({
							"sentence": sentence,
							"lu_pos": (int(target.get("start")), int(target.get("end"))+1)
						})

				yield el.get("ID"), el.get("name"), el.get("pos"), annotations
			except FileNotFoundError:
				yield el.get("ID"), el.get("name"), el.get("pos"), list()


	def parse_fes(self, root):
		for el in root.find("fes").findall("fe"):
			definition = self.clean_def(el.find("definition").text)
			yield (el.get("ID"), el.get("name"), None, el.get("coreType"),
				el.get("abbrev"), definition)


class SwedishFNLoader(FNLoader):

	@staticmethod
	def supported_db():
		return ['swedishfn']

	def __init__(self, db_name):
		super().__init__(db_name)
		self.id = 0

	def get_lu(self, lu):
		"""Returns the lexical unit and its part of speech in the BFN format, i.e.,
		POS tags are strings instead of numbers and its separated from the lemma by
		a single dot.

		:param lu: original Swedish FrameNet LU
		:type lu: str
		:returns: The LU, POS pair
		:rtype: tuple(str, str)
		"""
		pos = re.search(r'\.\.(\d+)', lu).group(1)
		lu = lu.replace('..', '.')
		return lu, pos

	def frames(self):
		filename = os.path.join("data", self.db_name, "data.xml")
		root = ET.parse(filename).getroot()

		for le in root.find("Lexicon").findall("LexicalEntry"):
			if le.find("Sense"):
				yield le.find("Sense")

	def parse_frame(self, root):
		try:
			en_name = next(f for f in root.findall("feat") if f.get("att") == "BFNID").get("val")
		except StopIteration:
			en_name = None
		self.id += 1
		return self.id, root.get("id"), en_name, None

	def parse_lus(self, root):
		for f in root.findall("feat"):
			if f.get("att") == "LU":
				lu, pos = self.get_lu(f.get("val"))
				self.id += 1
				yield self.id, lu, pos, []

	def parse_fes(self, root):
		for f in root.findall("feat"):
			if f.get("att") in SWEFN_FE_TYPES:
				self.id += 1
				yield self.id, None, f.get("val"), SWEFN_FE_TYPES[f.get("att")], None, None


loaders = [
	FNLoader,
	ChineseFNLoader,
	FNBrasilLoader,
	SwedishFNLoader,
]


def log_loaded_fn(fn):
	logger = logging.getLogger('alignment')

	logger.info(f'')
	logger.info(f"              Loaded '{fn.name}' database")
	logger.info(f'     frame count         = {len(fn.frames)}')
	logger.info(f'     lu count            = {sum(len(f.lus) for f in fn.frames)}')
	logger.info(f'     fe count            = {sum(len(f.fes) for f in fn.frames)}')
	logger.info(f'     lu annotation count = {sum(len(l.anno_sents) for f in fn.frames for l in f.lus)})')
	logger.info(f'')


def load(db_name, lang):
	"""This is a utility function that given ``db_name`` identifies the
	appropriate loader class (:class:`FNLoader` or a subclass) to handle this 
	database. An instance of this loader is used to create the FrameNet objects.

	:param db_name: The name of the database to be loaded.
	:type db_name: str
	:param lang: Language identifier to be attributed to loaded frames.
	:type lang: str
	:returns: pandas.DataFrame -- A pandas DataFrame containing all loaded frames.
	:raises: Exception
	"""
	loader = next(l(db_name) for l in loaders if db_name in l.supported_db())

	if not loader: 
		raise Exception(f"No loader found for db \"{db_name}\"")

	fn = loader.load(lang)
	log_loaded_fn(fn)

	return fn
