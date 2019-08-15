import xlrd
from xlrd.sheet import ctype_text
import agate
import numpy
import agatestats
import json


def remove_bad_chars(val):
	if val == '-':
		return None
	return val


def get_new_list(old_list, clean_func):
	new_list = []
	for evl in old_list:
		cleaned_vl = [clean_func(r) for r in evl]
		new_list.append(cleaned_vl)
	return new_list


def reverse_percent(row):
	return 100 - row['Total (%)']


def get_types(example_row):
	types = []
	for v in example_row:
		value_type = ctype_text[v.ctype]
		if value_type == "text":
			types.append(text_type)
		elif value_type == "number":
			types.append(number_type)
		elif value_type == "xldate":
			types.append(date_type)
		else:
			types.append(text_type)
	return types


def get_table(new_arr, types, titles):
	try:
		table = agate.Table(new_arr, titles, types)
		return table
	except Exception as e:
		return e


def float_to_str(x):
	try:
		return str(x)
	except Exception as e:
		return x
	
	
def get_country(country_row):
	return country_dict.get(country_row['Country / Territory'].lower())


def highest_rates(row):
	# if row['']
	if row['Total (%)'] > cl_mean and row['CPI 2013 Score'] < cpi_mean:
		return True
	return False

workbook = xlrd.open_workbook('data/chp9/unicef_oct_2014.xls')
sheet = workbook.sheets()[0]
title_rows = zip(sheet.row_values(4), sheet.row_values(5))
titles = [t[0] + ' ' + t[1] for t in title_rows]
titles = [t.strip() for t in titles]

coutry_rows = [sheet.row_values(r) for r in range(6, 114)]
cleaned_rows = get_new_list(coutry_rows, remove_bad_chars)

text_type = agate.Text()
number_type = agate.Number()
boolean_type = agate.Boolean()
date_type = agate.Date()

example_row = sheet.row(6)
unicef_types = get_types(example_row)
# types = []
# for v in example_row:
# 	value_type = ctype_text[v.ctype]
# 	if value_type == 'text':
# 		types.append(text_type)
# 	elif value_type == 'number':
# 		types.append(number_type)
# 	elif value_type == 'xldate':
# 		types.append(date_type)
# 	else:
# 		types.append(text_type)

table = agate.Table(cleaned_rows, titles, unicef_types)
# table.print_json(indent=4)
# 输出童工雇佣率最高的十个国家
most_egregious = table.order_by('Total (%)', reverse=True).limit(10)
# for r in most_egregious.rows:
# 	print(r)

# 输出女性童工雇佣率最高的十个国家
# most_female = table.order_by('Female', reverse=True).limit(10)
# for r in most_female.rows:
# 	print('{}: {}%'.format(r['Countries and areas'], r['Female']))
# female_data = table.where(lambda r: r['Female'] is not None)
# most_female = female_data.order_by('Female', reverse=True).limit(10)
# for r in most_female.rows:
# 	print('{}: {}%'.format(r['Countries and areas'], r['Female']))

# 计算Place of residence (%) Urban列的平均值
# table.aggregate(agate.Mean('Place of residence (%) Urban'))
# has_por = table.where(lambda r: r['Place of residence (%)Urban'] is not None)
# has_por.aggregate(agate.Mean('Place of residence (%)Urban'))
# 得出每行数据中农村童工雇佣率大于50%的数据
# first_match = has_por.find(lambda x: x['Rural'] > 50)
# print(first_match['Countries and areas'])

# 使用Total列数据对童工雇佣率最高的数据进行排序，从高到低
# ranked = table.compute([("Total Child Labor Rank", agate.Rank('Total (%)', reverse=True))])
# for row in ranked.order_by('Total (%)', reverse=True,).limit(20).rows:
# 	print(row['Total (%)'], row['Countries and areas'])
# 普通儿童占比
ranked = table.compute([("Children not working (%)", agate.Formula(number_type, reverse_percent))])
ranked = ranked.compute([("Total Child Labor Rank", agate.Rank("Children not working (%)"))])
# for row in ranked.order_by('Total (%)', reverse=True,).limit(20).rows:
# 	print(row['Total (%)'], row['Countries and areas'])
	
# 国际公开腐败感指数处理
cpi_workbook = xlrd.open_workbook('data/chp9/corruption_perception_index.xls')
cpi_sheet = cpi_workbook.sheets()[0]
# for r in range(cpi_sheet.nrows):
# 	print(r, cpi_sheet.row_values(r))

cpi_title_rows = zip(cpi_sheet.row_values(1), cpi_sheet.row_values(2))
cpi_titles = [t[0] + ' ' + t[1] for t in cpi_title_rows]
cpi_titles = [t.strip() for t in cpi_titles]
cpi_titles[0] = cpi_titles[0] + " Duplicate"
cpi_rows = [cpi_sheet.row_values(r) for r in range(3, cpi_sheet.nrows)]
cpi_rows = get_new_list(cpi_rows, float_to_str)
cpi_types = get_types(cpi_sheet.row(3))
cpi_table = get_table(cpi_rows, cpi_types, cpi_titles)

# 联结两表数据
cpi_and_cl = cpi_table.join(ranked, 'Country / Territory', 'Countries and areas', inner=True)
# for r in cpi_and_cl.order_by('CPI 2013 Score').limit(10).rows:
# 	print('{}: {} - {}%'.format(r['Country / Territory'], r['CPI 2013 Score'], r['Total (%)']))

# 识别相关性：负相关意味着，一个变量增长，另一个变量减小。
#            正相关意味着两个变量会同时增长或减小，
#            皮尔森相关系数在-1到1之间波动，0意味着无相关性，-1和1意味着相关性很强
relativity = numpy.corrcoef(
	[float(t) for t in cpi_and_cl.columns['Total (%)'].values()],
	[float(s) for s in cpi_and_cl.columns['CPI 2013 Score'].values()])[0, 1]
# print(relativity)

# 找出离群值 agate_stats
# std_outer_data = cpi_and_cl.stdev_outliers('Total (%)', deviations=5, reject=False)
# print(len(std_outer_data))
mad = cpi_and_cl.mad_outliers('Total (%)')
# for r in mad.rows:
# 	print(r['Country / Territory'], r['Total (%)'])

# 创建分组
with open('data/chp9/earth-cleaned.json', 'rb') as f:
	contents = f.read()
country_json = json.loads(contents)
country_dict = {}
for dct in country_json:
	country_dict[dct['name']] = dct['parent']


cpi_and_cl = cpi_and_cl.compute([('continent', agate.Formula(text_type, get_country)), ])
# for r in cpi_and_cl.rows:
# 	print(r['Country / Territory'], r['continent'])

# no_continent = cpi_and_cl.where(lambda x: x['continent'] is None)
# for r in no_continent.rows:
# 	print(r['Country / Territory'])
grp_by_cont = cpi_and_cl.group_by('continent')
# print(grp_by_cont)
# for cont, table in grp_by_cont.items():
# 	print(cont, len(table))
# agg = grp_by_cont.aggregate([
# 	('cl_mean', agate.Mean('Total (%)')),
# 	('cl_max', agate.Max('Total (%)')),
# 	('cpi_median', agate.Median('CPI 2013 Score')),
# 	('cpi_min', agate.Min('CPI 2013 Score'))
# ])
# agg.print_table()
# agg.print_bars('continent', 'cl_max')

# 分析数据
#  分离和聚焦数据
africa_cpi_cl = cpi_and_cl.where(lambda x: x['continent'] == 'africa')

# for r in africa_cpi_cl.order_by('Total (%)', reverse=True).rows:
# 	print("{}: {}% - {}%".format(r['Country / Territory'], r['Total (%)'], r['CPI 2013 Score']))
#
print(numpy.corrcoef(
	[float(t) for t in africa_cpi_cl.columns['Total (%)'].values()],
	[float(c) for c in africa_cpi_cl.columns['CPI 2013 Score'].values()])[0, 1]
)

africa_cpi_cl = africa_cpi_cl.compute([('Africa Child Labor Rank', agate.Rank('Total (%)', reverse=True)), ])
africa_cpi_cl = africa_cpi_cl.compute([('Africa CPI Rank', agate.Rank('CPI 2013 Score')), ])

cl_mean = africa_cpi_cl.aggregate(agate.Mean('Total (%)'))
cpi_mean = africa_cpi_cl.aggregate(agate.Mean('CPI 2013 Score'))
highest_cpi_cl = africa_cpi_cl.where(lambda x: highest_rates(x))

for r in highest_cpi_cl.rows:
	print("{}: {}% - {}".format(
		r['Country / Territory'],
		r['Total (%)'],
		r['CPI 2013 Score']
	))