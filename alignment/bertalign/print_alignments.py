import os
import random

def load_aligned_words(string):
	string = string.replace('\n', '')

	return [
		tuple(map(int, pair.split('-')))
		for pair in string.split(' ')
	]


def print_instance(a, b, align):
	words_a = a.split()
	words_b = b.split()

	print("------------------------------------------------------------")
	print("------------------------------------------------------------\n")
	print(a)
	print('-')
	print(b)
	for x in align:
		print(words_a[x[0]].ljust(20), words_b[x[1]])


sent_path = os.path.join("data", "fastalign-europarl.pt-en")
map_path = os.path.join("data", "fastalign-europarl.pt-en.intersect.align")

sent_fp = open(sent_path, 'r')
map_fp = open(map_path, 'r')

i = 0
print_count = 0
rng = random.Random()
while print_count < 100:
	a, b = next(sent_fp).split(" ||| ")
	align = next(map_fp)

	if rng.random() > 0.1:
		continue

	print_instance(a, b, load_aligned_words(align))
	print_count += 1

