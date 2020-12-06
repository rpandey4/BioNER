import os
import random
import xml.etree.ElementTree as ET
from nltk.tokenize import sent_tokenize
import math
import sys
import spacy

nlp = spacy.load('en_core_web_sm')


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


def get_cdr_masked_lm(file_path, output_folder, data_type, replace_type="all"):
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
    for lines in open(file_path):
        lines = lines.strip()
        if lines == "":
            sentences.append(" ".join(cur_sent))
            masked_sent = " ".join(cur_sent_negative)
            sentences_replaced.append(" ".join(cur_sent_replaced))
            sentences_negative.extend([text_neg for text_neg in get_combinations_sequences(masked_sent, SWAP_DICT) if text_neg not in sentences_replaced])
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


def get_cdr_masked_lm_with_other(file_path, output_folder, data_type, replace_type="all"):
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
    for lines in open(file_path):
        lines = lines.strip()
        if lines == "":
            sentences.append(" ".join(cur_sent))
            masked_sent = " ".join(cur_sent_negative)
            original_replaced_sent = " ".join(cur_sent_replaced)
            doc = nlp(original_replaced_sent)
            print("cur token:", cur_token)
            for token in doc:
                print(token.text, token.tag_)
            print(original_replaced_sent)
            sys.exit()
            sentences_replaced.append()
            sentences_negative.extend([text_neg for text_neg in get_combinations_sequences(masked_sent, SWAP_DICT) if text_neg not in sentences_replaced])
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
    # INP_PATH = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/MTL-Bioinformatics-2016/data/"
    INP_PATH = sys.argv[1]
    # OUT_PATH = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/data/bert-ready/MTL-Bioinformatics/Appropriate/BC5CDR"
    OUT_PATH = sys.argv[2]
    if not os.path.isdir(OUT_PATH):
        os.makedirs(OUT_PATH)
    # print([x for x in title_list if "." in x[:-2]])
    # print(title_list)
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-IOB", "train.tsv"), OUT_PATH, "train", "all")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-disease-IOB", "train.tsv"), OUT_PATH, "train", "disease")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-chem-IOB", "train.tsv"), OUT_PATH, "train", "chem")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-IOB", "devel.tsv"), OUT_PATH, "dev", "all")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-disease-IOB", "devel.tsv"), OUT_PATH, "dev", "disease")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-chem-IOB", "devel.tsv"), OUT_PATH, "dev", "chem")
    # get_cdr_lines(os.path.join(INP_PATH, "BC5CDR-IOB", "train.tsv"), title_list_new)
    # get_cdr_masked_lm_with_other(os.path.join(INP_PATH, "BC5CDR-chem-IOB", "train.tsv"), OUT_PATH, "train", "chem")
