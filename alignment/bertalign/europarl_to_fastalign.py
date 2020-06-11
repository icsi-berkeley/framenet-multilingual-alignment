import os
import tokenization

src_path = os.path.join("data", "europarl", "pt-en", "europarl-v7.pt-en.en")
tgt_path = os.path.join("data", "europarl", "pt-en", "europarl-v7.pt-en.pt")
out_path = os.path.join("data", "fastalign-europarl.pt-en")

src_fp = open(src_path, 'r')
tgt_fp = open(tgt_path, 'r')

tokenizer = tokenization.BasicTokenizer(do_lower_case=False)

with open(out_path, 'w') as out_fp:
	tokenize = lambda x: " ".join(tokenizer.tokenize(x))

	for src_sent, tgt_sent in zip(src_fp, tgt_fp):
		if src_sent and tgt_sent:
			src_tokens = tokenize(src_sent)
			tgt_tokens = tokenize(tgt_sent)
			
			if src_tokens and tgt_tokens:
				out_fp.write(f'{src_tokens} ||| {tgt_tokens}\n')

src_fp.close()
tgt_fp.close()