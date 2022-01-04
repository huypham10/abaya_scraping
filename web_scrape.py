#import packages

from selenium import webdriver as wb
import pandas as pd
import numpy as np
import urllib.request
import os
import time

from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_argument("--headless")


#set variables
main_website = 'https://en-ae.namshi.com/women-clothing-arabian_clothing-abayas'

#def
def extract_url_img(element):
	"""
	Get a listing's url and image url
	"""
	url_tag = element.find_element_by_tag_name('a')
	url = url_tag.get_attribute('href')
	img_tag = element.find_element_by_class_name('image_container').find_element_by_tag_name('img')
	if img_tag.get_attribute('data-src') == None:
		img = img_tag.get_attribute('src')
	else:
		img = img_tag.get_attribute('data-src')
	return url, img

def get_feature_dict(wbD, feature_xpath):
	"""
	Get a dictionary every value of a feature and the url that directs to all the listings with that feature
	e.g. an item in a color dictionary would be like {'yellow': 'www.url-that-directs-to-all-products-with-yellow-filter.com'}
	"""
	all_features = wbD.find_elements_by_xpath(feature_xpath)
	feature_list = [feature.text[:feature.text.rfind(" ")] for feature in all_features]
	feature_url_list = [feature.find_element_by_tag_name('a').get_attribute('href') for feature in all_features]
	
	return dict(zip(feature_list, feature_url_list))

def get_feature_url_dict(url=main_website):
	"""Get 3 dictionaries for color, occasion and style
	"""
	wbD = wb.Chrome('chromedriver.exe', options=chrome_options)
	wbD.get(url)

	color_dict = get_feature_dict(wbD, '//*[@id="catalog_filter_color_list"]/li')

	occasion_dict = get_feature_dict(wbD, '//*[@id="catalog_filter_occasion_list"]/li')

	style_dict = get_feature_dict(wbD, '//*[@id="catalog_filter_product_style_type_list"]/li')

	wbD.quit()
	return color_dict, occasion_dict, style_dict


def get_url_to_df(url, feature_para=""):
	"""
	Get all the listings' url and image url in the specified url
	"""
	df = pd.DataFrame(columns=["url", "img"])
	wbD = wb.Chrome('chromedriver.exe', options=chrome_options)
	wbD.get(f'{url}/{feature_para}')
	time.sleep(2)
	#get page 1 contents
	all_items = wbD.find_elements_by_xpath('//*[@id="catalog_listings"]/li')

	for item in all_items:
		url_, img_ = extract_url_img(item)
		df = df.append(pd.DataFrame([[url_, img_]], columns=df.columns), ignore_index=True)

	#get pages 2 to end
	page_no = int(wbD.find_element_by_xpath('//*[@id="pagination"]/p').text.split(" ")[-1])
	for no in range(2, page_no+1):
		wbD.get(f"{url}/page-{no}/{feature_para}")
		time.sleep(2)
		all_items = wbD.find_elements_by_xpath('//*[@id="catalog_listings"]/li')

		for item in all_items:
			url_, img_ = extract_url_img(item)
			df = df.append(pd.DataFrame([[url_, img_]], columns=df.columns), ignore_index=True)
	wbD.quit()
	return df


#create a dataframe containing url and image of all listings
main_df = get_url_to_df(main_website)
main_df['color'] = np.nan
main_df['occasion'] = np.nan
main_df['style'] = np.nan

color_dict, occasion_dict, style_dict = get_feature_url_dict()

#loop through all colors to create a dataframe for each color and then merge each color's dataframe onto the main dataframe 
for color, color_url in color_dict.items():
	color_df = get_url_to_df(color_url[:color_url.rfind("/")], color_url[color_url.rfind("/")+1:])
	print(color)
	main_df.loc[main_df['url'].isin(color_df['url']), 'color'] = color
	

#loop through all occasions to create a dataframe for each occasion and then merge each occasion's dataframe onto the main dataframe
for occasion, occasion_url in occasion_dict.items():
	occasion_df = get_url_to_df(occasion_url[:occasion_url.rfind("/")], occasion_url[occasion_url.rfind("/")+1:])
	print(occasion)
	main_df.loc[main_df['url'].isin(occasion_df['url']), 'occasion'] = occasion

#loop through all styles to create a dataframe for each style and then merge each style's dataframe onto the main dataframe
for style, style_url in style_dict.items():
	style_df = get_url_to_df(style_url[:style_url.rfind("/")], style_url[style_url.rfind("/")+1:])
	print(style)
	main_df.loc[main_df['url'].isin(style_df['url']), 'style'] = style

main_df.to_csv('features.csv')



# get images from url
os.makedirs("img", exist_ok=True) #create folder

for index, row in main_df['img'].iteritems():
    urllib.request.urlretrieve(row, f"img/{index}.jpg")
    


