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

def fe_matching(alignment, core_only=True):
	"""Computes the jaccard score of each frame pair in ``alignment`` based on
	core frame elements sets.

	:param alignment: An :class:`Alignment` instance.
	:type alignment: :class:`Alignment`
	:param core_only: If only core FEs should be considered for alignment.
	:type core_only: bool
	"""
	aid = 'core_fe_matching' if core_only else 'all_fe_matching'

	if core_only:
		aid = 'core_fe_matching'
		get_fes = lambda frm: set(
			fe.name_en or fe.name for fe in frm.fes if fe.type.lower() == "core")
	else:
		aid = 'all_fe_matching'
		get_fes = lambda frm: set(
			fe.name_en or fe.name for fe in frm.fes)

	fe_name_dict = {
		frm.gid: get_fes(frm)
		for frm in alignment.frm["obj"]
	}

	scores = []
	for frame, other in alignment.pairs():
		en_fes = fe_name_dict[frame.gid]
		l2_fes = fe_name_dict[other.gid]

		if len(en_fes) == 0 or len(l2_fes) == 0:
			scores.append(0)
		else:
			scores.append(len(en_fes & l2_fes) / len(en_fes | l2_fes))

	alignment.add_scores(aid, 'fe_matching', scores, desc=f'Matching core FEs')
