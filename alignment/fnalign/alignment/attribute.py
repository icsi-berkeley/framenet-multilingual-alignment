"""This module contains basic alignment procedures based on FrameNet elements's
attributes. This alignments should be mainly used as baselines for validation.

.. moduleauthor:: Arthur Lorenzi Almeida <lorenzi.arthur@gmail.com>
"""

def id_matching(alignment):
	"""Computes the alignment score of each frame pair in ``alignment``. When
	both frames have same ID, score = 1, else 0.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	"""
	scores = []
	for frame, other in alignment.pairs():
		scores.append(1 if frame.id == other.id else 0)
	
	alignment.add_scores(
		'id_matching', 'attr_matching', scores,
		desc=f'Matching ID')

def name_matching(alignment):
	"""Computes the alignment score of each frame pair in ``alignment``. When
	both frames have the same name, score = 1, else 0.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	"""
	scores = []
	for frame, other in alignment.pairs():
		scores.append(1 if frame.name == other.name or frame.name == other.name_en else 0)
	
	alignment.add_scores(
		'name_matching', 'attr_matching', scores,
		desc=f'Matching Name')

def fe_matching(alignment):
	"""Computes the jaccard score of each frame pair in ``alignment`` based on
	core frame elements sets.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	"""
	core_fes = {
		frm.gid: set(fe.name_en or fe.name for fe in frm.fes if fe.type.lower() == "core")
		for frm in alignment.frm["obj"]
	}

	scores = []
	for frame, other in alignment.pairs():
		en_fes = core_fes[frame.gid]
		l2_fes = core_fes[other.gid]

		if len(en_fes) == 0 or len(l2_fes) == 0:
			scores.append(0)
		else:
			scores.append(len(en_fes & l2_fes) / len(en_fes | l2_fes))

	alignment.add_scores(
		'core_fe_matching', 'fe_matching', scores,
		desc=f'Matching core FEs')

