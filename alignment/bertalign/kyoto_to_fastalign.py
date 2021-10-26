import os
import glob
import xml.etree.ElementTree as ET
import tokenization

src_path = os.path.join("data", "kyoto-wiki-corpus")
out_path = os.path.join("data", "kyoto-wiki-corpus", f"fastalign-kyoto-wiki.jp-en")

out_fp = open(out_path, 'w')

tokenizer = tokenization.BasicTokenizer(do_lower_case=False)
tokenize = lambda x: " ".join(tokenizer.tokenize(x))

for filepath in glob.glob(os.path.join(src_path, "*", "*.xml")):
	try:
		tree = ET.parse(filepath)

		for sen in tree.findall('.//sen'):
			src_sent = sen.find('j')
			tgt_sent = sen.find('e[@type="check"]')

			if src_sent.text is None:
				print(f'Japanese sentence with no text in file: {filepath}')
				continue

			if tgt_sent.text is None:
				print(f'English sentence with no text in file: {filepath}')
				continue

			src_tokens = tokenize(src_sent.text)
			tgt_tokens = tokenize(tgt_sent.text)
			
			out_fp.write(f'{src_tokens} ||| {tgt_tokens}\n')
	except ET.ParseError:
		print(f'Parsing failed for file: {filepath}')

out_fp.close()
