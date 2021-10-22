import os
from numpy.lib.function_base import average
import sklearn.metrics as metrics
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.metrics import PrecisionRecallDisplay

def read(dbname):
	path = os.path.join('data', 'gold', f'{dbname}.txt')

	with open(path, 'r') as fp:
		pairs = list(map(lambda l: tuple(l.split()), fp.readlines()))
	
	return pairs


def gold_scores(alignment):
	pairs = read(alignment.l2_fn.name)

	for score in alignment.scores:
		gold_df = score['df'].copy()

		gold_df[gold_df.columns] = 0

		for x, y in pairs:
			gold_df.loc[x, y] = 1

		true_values = gold_df.to_numpy().flatten()
		pred_values = score['df'].to_numpy().flatten()

		print('-------')
		print(score['id'])
		print('spearman')
		rho, p_value = stats.spearmanr(pred_values.argsort(), true_values.argsort())
		print(rho)
		print(p_value)
		print('kendall tau')
		tau, p_value = stats.kendalltau(pred_values.argsort(), true_values.argsort())
		print(tau)
		print(p_value)
		print('-------')

		precision, recall, _ = metrics.precision_recall_curve(true_values, pred_values)
		disp = PrecisionRecallDisplay(precision, recall, 0, score['id'])
		disp.plot()
		a = score['id']
		plt.savefig(f'plots/{a}.png')
		plt.close()

		# roc_auc = metrics.auc(precision, recall)

		# plt.title('Precision-recall curve')
		# plt.plot(precision, recall, 'b', label = 'AUC = %0.2f' % roc_auc)
		# plt.legend(loc = 'lower right')
		# plt.plot([0, 1], [0, 1],'r--')
		# plt.xlim([0, 1])
		# plt.ylim([0, 1])
		# plt.ylabel('Recall')
		# plt.xlabel('Precision')
		# a = score['id']
		# plt.savefig(f'{a}.png')
		# plt.close()


		print('boa')



# print(read('salsa'))