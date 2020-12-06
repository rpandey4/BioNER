import os
import random
import xml.etree.ElementTree as ET
from nltk.tokenize import sent_tokenize
import math
import sys
import spacy

nlp = spacy.load('en_core_web_sm')


class get_binary_array:
    full_array = []
    def printTheArray(arr, n):  
    
        for i in range(0, n):  
            print(arr[i], end = " ")  
        
        print() 
    
    # Function to generate all binary strings  
    def generateAllBinaryStrings(self, n, arr, i):  
    
        if i == n: 
            self.full_array.append([x for x in arr])
            return
        
        # First assign "0" at ith position  
        # and try for all other permutations  
        # for remaining positions  
        arr[i] = 0
        self.generateAllBinaryStrings(n, arr, i + 1)  
    
        # And then assign "1" at ith position  
        # and try for all other permutations  
        # for remaining positions  
        arr[i] = 1
        self.generateAllBinaryStrings(n, arr, i + 1)  
    
    # Driver Code  
    def __init__(self, n): 
        arr = [None] * n  
        self.generateAllBinaryStrings(n, arr, 0)
        return

    
    def get_full_array(self):
        random.shuffle(self.full_array)
        return self.full_array


def get_combinations_sequences(text_for_bert, label_list, kkk=5):
    cur_seq_list = text_for_bert.split("[MASK]")
    k = len(cur_seq_list)-1
    tot_sequences = math.pow(len(label_list), k)
    all_sequences_list = []
    count = 0
    while (count < tot_sequences):
        tmp_list = []
        for i in range(k):
            tmp_list.append(random.choice(label_list))
        if tmp_list in all_sequences_list:
            continue
        all_sequences_list.append(tmp_list)
        if len(all_sequences_list) > kkk:
            break
        count += 1
    text_neg_list = []
    # print("Total negative", len(all_sequences_list))
    for j in range(len(all_sequences_list)):
        seq = all_sequences_list[j]
        new_seq_list = [cur_seq_list[0]]
        for i in range(k):
            new_seq_list.append(seq[i])
            new_seq_list.append(cur_seq_list[i+1])
        text_neg_list.append("".join(new_seq_list).strip())
    # print("Masked Sent: %s\n\nOutput Negatives:\n%s\n%s\n" % (text_for_bert, "\n".join(text_neg_list), "*"*100))
    return text_neg_list

def get_positive_combination_sequences(original_replaced_sent, tmp_combinations_dict, SWAP_DICT, kkk=5, max_tokens=24):
    doc = nlp(original_replaced_sent)
    token_to_change = []
    for i in range(len(doc)):
        token = doc[i]
        if token.text not in SWAP_DICT and token.tag_.startswith("NN"):
            token_to_change.append(i)
        # print(token.text, token.tag_)
    # print(original_replaced_sent)
    # print(token_to_change)
    token_to_change = token_to_change[:max_tokens]
    tmp_combinations = [x for x in tmp_combinations_dict[len(token_to_change)]]
    random.shuffle(tmp_combinations)
    # if len(tmp_combinations) < kkk:
    #     print(len(token_to_change), " itta tha")
    #     print(tmp_combinations)
    combinations = []
    for k in range(min(kkk, len(tmp_combinations))):
        combinations.append(tmp_combinations.pop())
    new_sent = []
    for cmb_list in combinations:
        tmp_sent = []
        for i in range(len(doc)):
            tmp_sent.append(doc[i].text)
        for j in range(len(token_to_change)):
            try:
                if cmb_list[j] == 1:
                    tmp_sent[token_to_change[j]] = "other"
            except Exception as e:
                print(cmb_list)
                print([len(z) for z in combinations])
                print("j", j, " | len", len(cmb_list), "token_to_change", len(token_to_change))
                print(e)
                sys.exit()
        new_sent.append(" ".join(tmp_sent))
    return new_sent


def get_cdr_masked_lm_with_other(file_path, output_folder, tmp_combinations_dict, data_type, replace_type="all"):
    sentences = []
    sentences_replaced = []
    sentences_negative = []
    cur_sent = []
    cur_sent_replaced = []
    cur_sent_negative = []
    cur_token = ""
    title_cnt = 0
    SWAP_DICT = ["disease", "chemical", "other"]
    map_token_concepts = {"B-Disease": "disease", "B-Chemical": "chemical", "I-Disease": "disease", "I-Chemical": "chemical"}
    tot_sent = 0
    for lines in open(file_path):
        lines = lines.strip()
        if lines == "":
            sentences.append(" ".join(cur_sent))
            masked_sent = " ".join(cur_sent_negative)
            sentences_replaced.extend(get_positive_combination_sequences(" ".join(cur_sent_replaced), tmp_combinations_dict, SWAP_DICT))
            sentences_negative.extend([text_neg for text_neg in get_combinations_sequences(masked_sent, SWAP_DICT) if text_neg not in sentences_replaced])
            tot_sent += 1
            # print("Sentence %d done. Total positive sentences = %d. Total negative sentences = %d" % (tot_sent, len(sentences_replaced), len(sentences_negative)))
            # print(sentences_replaced)
            # print(sentences_negative)
            # sys.exit()
            cur_sent = []
            cur_sent_replaced = []
            cur_sent_negative = []
            continue
        lines = lines.split("\t")
        cur_sent.append(lines[0])
        if lines[1] == "O":
            if cur_token:
                cur_sent_replaced.append(cur_token)
                cur_sent_negative.append("[MASK]")
                cur_token = ""
            cur_sent_replaced.append(lines[0])
            cur_sent_negative.append(lines[0])
        else:
            if lines[1].startswith("B-") and cur_token:
                cur_sent_replaced.append(cur_token)
                cur_sent_negative.append("[MASK]")
            cur_token = map_token_concepts[lines[1]]
    # for i in range(len(sentences)):
    out_file = os.path.join(output_folder, "cdr_data_%s_%s_replaced_appropriateness.csv" % (data_type, replace_type))
    print("Now writing for %s type %s replace type %s" % (os.path.basename(file_path), data_type, replace_type))
    all_sent = []
    all_sent.extend([(x, "appropriate") for x in sentences_replaced])
    all_sent.extend([(x, "not-appropriate") for x in sentences_negative])
    random.shuffle(all_sent)
    random.shuffle(all_sent)
    with open(out_file, "w") as f:
        for text, label in all_sent:
            f.write("%s\t%s\n" % (text, label))
    return



if __name__ == "__main__":
    INP_PATH = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/MTL-Bioinformatics-2016/data/"
    OUT_PATH = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/data/bert-ready/MTL-Bioinformatics/Appropriate/OTHERS_INCLUDED/BC5CDR"
    if not os.path.isdir(OUT_PATH):
        os.makedirs(OUT_PATH)
    tmp_combinations_dict = {0: []}
    for i in range(1, 25):
        gba = get_binary_array(i)
        tmp_combinations_dict[i] = [x for x in gba.get_full_array() if len(x) == i]
        print("Store combinations of %d array" % (i+1))
    # print([x for x in title_list if "." in x[:-2]])
    # print(title_list)
    get_cdr_masked_lm_with_other(os.path.join(INP_PATH, "BC5CDR-IOB", "train.tsv"), OUT_PATH, tmp_combinations_dict, "train", "all")
    get_cdr_masked_lm_with_other(os.path.join(INP_PATH, "BC5CDR-disease-IOB", "train.tsv"), OUT_PATH, tmp_combinations_dict, "train", "disease")
    get_cdr_masked_lm_with_other(os.path.join(INP_PATH, "BC5CDR-chem-IOB", "train.tsv"), OUT_PATH, tmp_combinations_dict, "train", "chem")
    get_cdr_masked_lm_with_other(os.path.join(INP_PATH, "BC5CDR-IOB", "devel.tsv"), OUT_PATH, tmp_combinations_dict, "dev", "all")
    get_cdr_masked_lm_with_other(os.path.join(INP_PATH, "BC5CDR-disease-IOB", "devel.tsv"), OUT_PATH, tmp_combinations_dict, "dev", "disease")
    get_cdr_masked_lm_with_other(os.path.join(INP_PATH, "BC5CDR-chem-IOB", "devel.tsv"), OUT_PATH, tmp_combinations_dict, "dev", "chem")
    # get_cdr_lines(os.path.join(INP_PATH, "BC5CDR-IOB", "train.tsv"), title_list_new)
    # get_cdr_masked_lm_with_other(os.path.join(INP_PATH, "BC5CDR-chem-IOB", "train.tsv"), OUT_PATH, "train", "chem")
