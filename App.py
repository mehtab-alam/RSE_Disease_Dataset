import streamlit as st
import pandas as pd
import re
from spacy.lang.en import English
import spacy
from gensim.parsing.preprocessing import remove_stopwords
from spacy import displacy
import os
import time
import math
import shutil


HTML_WRAPPER = """<div style="overflow-x: auto; border: none solid #e6e9ef; border-radius: 0.25rem; padding: 1rem">{}</div>"""

HTML = "<a href='https://www.teacheron.com/tutor-profile/4uQK?r=4uQK' target='_blank' style='display: inline-block;'><img src='https://www.teacheron.com/resources/assets/img/badges/viewMyProfile.png' style='width: 336px !important; height: 144px !important'></a>"


def removeStopwords(text):
    return remove_stopwords(text)

@st.cache(allow_output_mutation=True)
def init_custom_ner():
    nlp = English()
    ruler = nlp.add_pipe("entity_ruler", config={"validate": True})
    ruler.from_disk("pipeline/entity_ruler/")
    return nlp

#@st.cache(suppress_st_warning=True)
def rsi_extraction(listText):
    nlp = init_custom_ner()
    rsi_list = list()
    
    #print(str(listText)[1:-1])
    
    #rsi_list.append("eastern Senegal")
    #return rsi_list


    doc = nlp(removeStopwords(str(listText)[1:-1]))
    
    ents = list()
    for entity in doc.ents:
        ents.append(entity.text)
    rsi_list.extend(ents)
   
    #html = displacy.render(doc,style="ent")
    #html = html.replace("\n","")
    #st.write(HTML_WRAPPER.format(html),unsafe_allow_html=True)
   
    return rsi_list

def get_total_count(inter,total):
    rsi_comm_total = 0 
    for ob in inter:
        rsi_comm_total = rsi_comm_total + total.count(ob)
    
    return rsi_comm_total

def write_rsi_logs(disease_name, rsi_actual, rsi_extracted_list):
    path = "logs"+ os.sep + disease_name+'.txt'
    if os.path.exists(path):
        os.remove(path)
    with open(path, 'w') as f:
        f.write(disease_name+"\n")
        f.write("\n\nNo. of Total RSI:"+ str(len(rsi_actual))+"\n")
        f.write("RSI Actual List :\n")
        f.write(str(rsi_actual)+"\n")
        f.write("\n\nNo. of Extracted RSI:"+ str(len(rsi_extracted_list))+"\n")
        f.write("RSI Extracted List :\n")
        f.write(str(rsi_extracted_list)+"\n")


    
def main():

    st.set_page_config(layout="wide")
    
    st.error("Make sure you have empty log directory in your script folder...")
    st.title("RSI Evaluation")
    uploaded_files = st.file_uploader("Choose dataset CSV files", type=None, accept_multiple_files=True)

    diseases_list = list()
    articles_list = list()
    rsi_extracted_list = list()
    rsi_actual_list = list()
    precision_list = list()
    recall_list = list()
    fscore_list = list()
    replace_list = ['.csv', 'articles_','_2020']
    if st.button('Evaluate'):
        start_time = time.time()
        for uploaded_file in uploaded_files:
            disease_rsi_actual = list()
            disease_name= re.sub(r'|'.join(map(re.escape, replace_list)), '', 
                                 uploaded_file.name)
            
            if disease_name == 'TBE':
                disf = pd.read_csv(uploaded_file, encoding="ISO-8859-1", engine='python')
            else:
                disf = pd.read_csv(uploaded_file, encoding="utf-8", engine='python')
            disf = disf.replace(r'\n',' ', regex=True) 
          
            
            list_text = disf['text'].tolist()
            rse_valid = disf['rse'] != '#'
            
            disf_actual = disf[rse_valid]
            for i, row in disf_actual.iterrows():
                rsi_actual = row['rse'].split(',')
                rsi_actual= [i.strip() for i in rsi_actual]
                disease_rsi_actual.extend(rsi_actual)
            
            extracted_rsi = rsi_extraction(list_text)
            
            list_interesection = list(set(extracted_rsi).intersection(disease_rsi_actual))
            corr_rsi = get_total_count(list_interesection, extracted_rsi)
            
            print("Disease Name:"+ disease_name)
            print("RSI Actual:"+ str(disease_rsi_actual))
            print("RSI Extracted:"+ str(extracted_rsi))
            print("Corrected RSI:"+ str(corr_rsi))
            
            diseases_list.append(disease_name)
            articles_list.append(disf.shape[0])
            rsi_extracted_list.append(len(extracted_rsi))
            rsi_actual_list.append(len(disease_rsi_actual))
            
            precision = corr_rsi/len(extracted_rsi)
            precision_list.append(precision)
            
            recall =  corr_rsi/len(disease_rsi_actual)
            recall_list.append(recall)
            
            fscore = (2*precision*recall)/(precision+recall)
            fscore_list.append(fscore)
            #print(len(disease_rsi_actual))
            #print(str(disease_rsi_actual))
            
            write_rsi_logs(disease_name, disease_rsi_actual, extracted_rsi)
        
        
        st.markdown("Total time taken: **_"+ str(round((time.time() - start_time)/60, 2))+" minutes_**")
        
        df = pd.DataFrame({"Disease Name": diseases_list, "No. of Articles": articles_list
                           ,"RSI Extracted": rsi_extracted_list, "RSI Actual": rsi_actual_list, 
                           "Precision": precision_list
                           ,"Recall": recall_list, "F-Score": fscore_list})
        st.write(df.round(2).astype("str"))
        st.success(str(diseases_list)+" logs are created to see the details")
        
         
if __name__ == '__main__':
	main()	