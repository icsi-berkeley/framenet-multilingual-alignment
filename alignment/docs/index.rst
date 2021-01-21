.. MLFN Alignment documentation master file, created by
   sphinx-quickstart on Tue Dec 10 15:25:19 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to MLFN Alignment's documentation!
==========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. automodule:: fnalign
   :members:

Models
======

.. automodule:: fnalign.models
   :members: Frame,LU,Alignment


Loaders
=======

.. automodule:: fnalign.loaders
   :members: load,FNLoader,ChineseFNLoader,FNBrasilLoader

Aligners
========

All functions that effectively align FrameNets are expected to receive an
:class:`Alignment` object as parameter and mutate it. This interface is not
implemented explicitly yet because I'm still not sure what its API should be.
For now, assuming that alignment algorithm are very different from each other,
the only rules are those two mentioned.

*******
Wordnet
*******

.. automodule:: fnalign.alignment.wordnet
   :members: synset_matching,lu_matching,get_mappings,get_synsets,set_resources

*********************************************************
Vectors - MUSE and BERT
*********************************************************

.. automodule:: fnalign.alignment.vectors
   :members:

*******************
FrameNet attributes
*******************

.. automodule:: fnalign.alignment.attribute
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
