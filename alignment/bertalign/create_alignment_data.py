import os
import collections
import itertools
import random
import string

import numpy as np
import tensorflow as tf
from bert_serving.client import BertClient

import modeling
import tokenization


flags = tf.flags
FLAGS = flags.FLAGS

flags.DEFINE_string("input_sentence_file", None,
										"Input aligned sentences file.")

flags.DEFINE_string("input_mapping_file", None,
										"Input word mappings of the aligned sentences.")

flags.DEFINE_string(
		"output_file", None,
		"Output TF example file (or comma-separated list of files).")

flags.DEFINE_integer("random_seed", 12345, "Random seed for data generation.")

flags.DEFINE_integer("sample_size", None, "Size of the dataset sample.")

flags.DEFINE_string(
		"bert_config_file", None,
		"The config json file corresponding to the pre-trained BERT model. "
		"This specifies the model architecture.")

flags.DEFINE_integer(
		"max_seq_length", 128,
		"The maximum total input sequence length after WordPiece tokenization. "
		"Sequences longer than this will be truncated, and sequences shorter "
		"than this will be padded.")

flags.DEFINE_string(
		"init_checkpoint", None,
		"Initial checkpoint (usually from a pre-trained BERT model).")

flags.DEFINE_string("vocab_file", None,
										"The vocabulary file that the BERT model was trained on.")

flags.DEFINE_bool(
		"do_lower_case", True,
		"Whether to lower case the input text. Should be True for uncased "
		"models and False for cased models.")

flags.DEFINE_integer("batch_size", 32, "Batch size for predictions.")

flags.DEFINE_bool("use_tpu", False, "Whether to use TPU or GPU/CPU.")

flags.DEFINE_string("master", None,
										"If using a TPU, the address of the master.")

flags.DEFINE_integer(
		"num_tpu_cores", 8,
		"Only used if `use_tpu` is True. Total number of TPU cores to use.")

flags.DEFINE_bool(
		"use_one_hot_embeddings", False,
		"If True, tf.one_hot will be used for embedding lookups, otherwise "
		"tf.nn.embedding_lookup will be used. On TPUs, this should be True "
		"since it is much faster.")


class TrainingInstance(object):
	"""A single training instance (sentence pair)."""

	def __init__(self, tokens, segment_ids, aligned_lm_positions_a,
							 aligned_lm_positions_b, aligned_lm_mask):
		self.tokens = tokens
		self.segment_ids = segment_ids
		self.aligned_lm_positions_a = aligned_lm_positions_a
		self.aligned_lm_positions_b = aligned_lm_positions_b
		self.aligned_lm_mask = aligned_lm_mask


def file_len(path):
	with open(path) as f:
		i = 0
		for i, l in enumerate(f):
			pass

	return i + 1

def get_sample(input_sentence_file, input_mapping_file, rng, n=1000):
	data_size = file_len(input_sentence_file)
	assert data_size == file_len(input_mapping_file)

	return rng.sample(range(0, data_size), n)


def data_reader(input_sentence_file, input_mapping_file, sample):
	sent_reader = tf.gfile.GFile(input_sentence_file, "r")
	map_reader = tf.gfile.GFile(input_mapping_file, "r")

	sent_line = sent_reader.readline()
	map_line = map_reader.readline()

	if sample:
		i = 0
		while sent_line and map_line:
			if i in sample:
				yield sent_line, map_line

			i += 1
			sent_line = sent_reader.readline()
			map_line = map_reader.readline()
	else:
		while sent_line and map_line:
			yield sent_line, map_line
			sent_line = sent_reader.readline()
			map_line = map_reader.readline()


def load_aligned_words(line):
	line = line.replace('\n', '')

	try:
		return [
			tuple(map(int, pair.split('-')))
			for pair in line.split(' ')
		]
	except ValueError:
		raise Exception(f'ue: {line}.')


def get_tokenized_word_map(align, tokenized_a, tokenized_b):
	cum_a = list(itertools.accumulate([len(t)-1 for t in tokenized_a]))
	cum_b = list(itertools.accumulate([len(t)-1 for t in tokenized_b]))

	return [
		(x[0]+cum_a[x[0]], x[1]+cum_b[x[1]])
		for x in align
	]



def truncate_seq_pair(tokens_a, tokens_b, max_num_tokens, rng):
	"""Truncates a pair of sequences to a maximum sequence length."""
	shift = { 'a': 0, 'b': 0 }

	while True:
		total_length = len(tokens_a) + len(tokens_b)
		if total_length <= max_num_tokens:
			break

		if len(tokens_a) > len(tokens_b):
			pos = 'a'
			trunc_tokens = tokens_a
		else:
			pos = 'b'
			trunc_tokens = tokens_b

		assert len(trunc_tokens) >= 1

		# We want to sometimes truncate from the front and sometimes from the
		# back to add more randomness and avoid biases.
		if rng.random() < 0.5:
			shift[pos] -= 1
			del trunc_tokens[0]
		else:
			trunc_tokens.pop()

	return shift['a'], shift['b']


def align_filter(align, a, b):
	return (
		a[align[0]] != b[align[1]]
		or (not a[align[0]].isnumeric() and a[align[0]] not in string.punctuation)
	)


def is_valid_range(align, len_a, len_b):
	return not (
		align[0] < 0
		or align[1] < 0
		or align[0] >= len_a
		or align[1] >= len_b
	)


def create_int_feature(values):
	feature = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
	return feature


def create_float_feature(values):
	feature = tf.train.Feature(float_list=tf.train.FloatList(value=list(values)))
	return feature


def model_fn_builder(bert_config, init_checkpoint, use_tpu,
										 use_one_hot_embeddings):
	"""Returns `model_fn` closure for TPUEstimator."""

	def model_fn(features, labels, mode, params):  # pylint: disable=unused-argument
		"""The `model_fn` for TPUEstimator."""

		input_ids = features["input_ids"]
		input_mask = features["input_mask"]
		input_type_ids = features["input_type_ids"]

		model = modeling.BertModel(
				config=bert_config,
				is_training=False,
				input_ids=input_ids,
				input_mask=input_mask,
				token_type_ids=input_type_ids,
				use_one_hot_embeddings=use_one_hot_embeddings)

		if mode != tf.estimator.ModeKeys.PREDICT:
			raise ValueError("Only PREDICT modes are supported: %s" % (mode))

		tvars = tf.trainable_variables()
		scaffold_fn = None
		(assignment_map,
		 initialized_variable_names) = modeling.get_assignment_map_from_checkpoint(
				 tvars, init_checkpoint)
		if use_tpu:

			def tpu_scaffold():
				tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
				return tf.train.Scaffold()

			scaffold_fn = tpu_scaffold
		else:
			tf.train.init_from_checkpoint(init_checkpoint, assignment_map)

		tf.logging.info("**** Trainable Variables ****")
		for var in tvars:
			init_string = ""
			if var.name in initialized_variable_names:
				init_string = ", *INIT_FROM_CKPT*"
			tf.logging.info("  name = %s, shape = %s%s", var.name, var.shape,
											init_string)

		predictions = { "layer_output": model.get_all_encoder_layers()[-1] }

		output_spec = tf.contrib.tpu.TPUEstimatorSpec(
				mode=mode, predictions=predictions, scaffold_fn=scaffold_fn)
		return output_spec

	return model_fn


def get_embedding_estimator():
	bert_config = modeling.BertConfig.from_json_file(FLAGS.bert_config_file)

	is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2
	run_config = tf.contrib.tpu.RunConfig(
			master=FLAGS.master,
			tpu_config=tf.contrib.tpu.TPUConfig(
					num_shards=FLAGS.num_tpu_cores,
					per_host_input_for_training=is_per_host))

	model_fn = model_fn_builder(
			bert_config=bert_config,
			init_checkpoint=FLAGS.init_checkpoint,
			use_tpu=FLAGS.use_tpu,
			use_one_hot_embeddings=FLAGS.use_one_hot_embeddings)

	# If TPU is not available, this will fall back to normal Estimator on CPU
	# or GPU.
	estimator = tf.contrib.tpu.TPUEstimator(
			use_tpu=FLAGS.use_tpu,
			model_fn=model_fn,
			config=run_config,
			predict_batch_size=FLAGS.batch_size)

	return estimator


def input_fn_builder(instances, tokenizer, max_seq_length):
	"""Creates an `input_fn` closure to be passed to TPUEstimator."""

	all_input_ids = []
	all_input_mask = []
	all_input_type_ids = []

	for instance in instances:
		input_ids = tokenizer.convert_tokens_to_ids(instance.tokens)
		input_mask = [1] * len(input_ids)
		segment_ids = instance.segment_ids.copy()

		while len(input_ids) < max_seq_length:
			input_ids.append(0)
			input_mask.append(0)
			segment_ids.append(0)

		all_input_ids.append(input_ids)
		all_input_mask.append(input_mask)
		all_input_type_ids.append(segment_ids)

	def input_fn(params):
		"""The actual input function."""
		batch_size = params["batch_size"]

		num_examples = len(instances)

		# This is for demo purposes and does NOT scale to large data sets. We do
		# not use Dataset.from_generator() because that uses tf.py_func which is
		# not TPU compatible. The right way to load data is with TFRecordReader.
		d = tf.data.Dataset.from_tensor_slices({
				"input_ids":
						tf.constant(
								all_input_ids, shape=[num_examples, max_seq_length],
								dtype=tf.int32),
				"input_mask":
						tf.constant(
								all_input_mask,
								shape=[num_examples, max_seq_length],
								dtype=tf.int32),
				"input_type_ids":
						tf.constant(
								all_input_type_ids,
								shape=[num_examples, max_seq_length],
								dtype=tf.int32),
		})

		d = d.batch(batch_size=batch_size, drop_remainder=False)
		return d

	return input_fn


def get_pretrained_embeddings(estimator, instances, tokenizer):
	input_fn = input_fn_builder(
			instances=instances, tokenizer=tokenizer, max_seq_length=FLAGS.max_seq_length)

	return [
		result["layer_output"]
		for result in estimator.predict(input_fn, yield_single_examples=True)
	]


def write_instance_to_example_files(instances, tokenizer, max_seq_length,
																		writers, estimator):
	"""Create TF example files from `TrainingInstance`s."""
	token_map_size = int(max_seq_length / 2)

	writer_index = 0
	total_written = 0
	pretrain_emb = get_pretrained_embeddings(estimator, instances, tokenizer)

	for (inst_index, instance) in enumerate(instances):
		input_ids = tokenizer.convert_tokens_to_ids(instance.tokens)
		input_mask = [1] * len(input_ids)
		segment_ids = list(instance.segment_ids)
		aligned_lm_positions_a = list(instance.aligned_lm_positions_a)
		aligned_lm_positions_b = list(instance.aligned_lm_positions_b)
		aligned_lm_mask = list(instance.aligned_lm_mask)
		assert len(input_ids) <= max_seq_length

		while len(input_ids) < max_seq_length:
			input_ids.append(0)
			input_mask.append(0)
			segment_ids.append(0)

		while len(aligned_lm_mask) < token_map_size:
			aligned_lm_positions_a.append(0)
			aligned_lm_positions_b.append(0)
			aligned_lm_mask.append(0)

		assert len(input_ids) == max_seq_length
		assert len(input_mask) == max_seq_length
		assert len(segment_ids) == max_seq_length
		assert len(aligned_lm_positions_a) == token_map_size
		assert len(aligned_lm_positions_b) == token_map_size
		assert len(aligned_lm_mask) ==  token_map_size

		features = collections.OrderedDict()
		features["input_ids"] = create_int_feature(input_ids)
		features["input_mask"] = create_int_feature(input_mask)
		features["segment_ids"] = create_int_feature(segment_ids)
		features["aligned_lm_positions_a"] = create_int_feature(aligned_lm_positions_a)
		features["aligned_lm_positions_b"] = create_int_feature(aligned_lm_positions_b)
		features["aligned_lm_mask"] = create_float_feature(aligned_lm_mask)
		features["pretrain_embedding"] = create_float_feature(pretrain_emb[inst_index].reshape(-1))

		tf_example = tf.train.Example(features=tf.train.Features(feature=features))

		writers[writer_index].write(tf_example.SerializeToString())
		writer_index = (writer_index + 1) % len(writers)

		total_written += 1

		if inst_index < 5:
			tf.logging.info("*** Example ***")
			tf.logging.info("tokens: %s" % " ".join(
					[tokenization.printable_text(x) for x in instance.tokens]))

			for feature_name in features.keys():
				if feature_name == 'pretrain_embedding':
					continue

				feature = features[feature_name]
				values = []
				if feature.int64_list.value:
					values = feature.int64_list.value
				elif feature.float_list.value:
					values = feature.float_list.value
				tf.logging.info(
						"%s: %s" % (feature_name, " ".join([str(x) for x in values])))

	tf.logging.info("Wrote %d total instances", total_written)


def create_training_instances(input_sentence_file, input_mapping_file,
															tokenizer, max_seq_length, rng, do_lower_case,
															sample=None):
	instances = []
	reader = data_reader(input_sentence_file, input_mapping_file, sample)
	
	for sent_line, map_line in reader:
		line = tokenization.convert_to_unicode(sent_line)

		if line.strip() and map_line.strip():
			a, b = line.split(" ||| ")
			mapping = load_aligned_words(map_line)

			instances.append(create_instance(a, b, mapping, tokenizer, max_seq_length,
				rng, do_lower_case))

	return instances


def create_instance(a, b, align, tokenizer, max_seq_length, rng, do_lower_case):
	# Account for [CLS], [SEP], [SEP]
	max_num_tokens = max_seq_length - 3

	words_a = a.split()
	words_b = b.split()

	if do_lower_case:
		words_a = [w.lower() for w in words_a]
		words_b = [w.lower() for w in words_b]

	tokenized_a = [tokenizer.tokenize(t) for t in words_a]
	tokenized_b = [tokenizer.tokenize(t) for t in words_b]

	tokens_a = [s for t in tokenized_a for s in t]
	tokens_b = [s for t in tokenized_b for s in t]

	shift_a, shift_b = truncate_seq_pair(tokens_a, tokens_b, max_num_tokens, rng)

	# fixes word alignment positions after tokenization and truncation
	shifted_align = (
		(x[0]+shift_a, x[1]+shift_b)
		for x in get_tokenized_word_map(align, tokenized_a, tokenized_b)
	)

	# remove out of range positions (because tokens were removed)
	truncated_align = (
		x for x in shifted_align
		if is_valid_range(x, len(tokens_a), len(tokens_b))
	)

	# remove punctuation token alignments
	instance_align = [
		(x[0]+1, x[1]+len(tokens_a)+2)
		for x in truncated_align
		if align_filter(x, tokens_a, tokens_b)
	]

	tokens = ["[CLS]"] + tokens_a + ["[SEP]"] + tokens_b + ["[SEP]"]
	segment_ids = [0] * (len(tokens_a) + 2) + [1] * (len(tokens_b) + 1)

	aligned_lm_positions_a = []
	aligned_lm_positions_b = []

	for align in instance_align:
		aligned_lm_positions_a.append(align[0])
		aligned_lm_positions_b.append(align[1])

	aligned_lm_mask = [1] * len(instance_align)

	return TrainingInstance(
		tokens=tokens,
		segment_ids=segment_ids,
		aligned_lm_positions_a=aligned_lm_positions_a,
		aligned_lm_positions_b=aligned_lm_positions_b,
		aligned_lm_mask=aligned_lm_mask
	)


def main(_):
	tf.logging.set_verbosity(tf.logging.INFO)

	output_files = FLAGS.output_file.split(",")
	writers = [tf.python_io.TFRecordWriter(out) for out in output_files]

	rng = random.Random(FLAGS.random_seed)

	tokenizer = tokenization.WordpieceTokenizer(
			vocab=tokenization.load_vocab(FLAGS.vocab_file))

	estimator = get_embedding_estimator()

	sample = get_sample(FLAGS.input_sentence_file, FLAGS.input_mapping_file,
		rng, FLAGS.sample_size)
	batches = list(range(0, len(sample), 3000)) + [len(sample)]

	for brange in zip(batches, batches[1:]):
		batch_sample = sample[brange[0]:brange[1]]

		instances = create_training_instances(
			FLAGS.input_sentence_file, FLAGS.input_mapping_file, tokenizer,
			FLAGS.max_seq_length, rng, FLAGS.do_lower_case, batch_sample)

		write_instance_to_example_files(instances, tokenizer, FLAGS.max_seq_length,
																		writers, estimator)

	for writer in writers:
		writer.close()


if __name__ == "__main__":
	flags.mark_flag_as_required("input_sentence_file")
	flags.mark_flag_as_required("input_mapping_file")
	flags.mark_flag_as_required("output_file")
	flags.mark_flag_as_required("vocab_file")
	flags.mark_flag_as_required("sample_size")
	tf.app.run()