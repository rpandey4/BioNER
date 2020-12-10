import json
import sys
from collections import defaultdict
import xml.etree.ElementTree as ET
import os
import pickle
import re
import random
import math
import spacy


nlp = spacy.load("en")


# #############
# disease: _d1s_
# gene: _g1e_
# drugs/chemical: _c1l_
# #############


def prepare_spans(text, annotations, pick_random=False):
    result_spans = {}
    span_list = []
    f_ovlp_cnt = 0
    amb_spans = defaultdict(list)
    for ann in annotations:
        span = tuple(ann["spans"][0])
        # print("annotation %s | label %s | actual gloss %s" % (text[span[0]:span[1]],
        #                                                       ann['type'], ann["gloss"]), " |", span)
        result_spans[span] = {"type": "none",
                              "label": ann['type'], "gloss": ann["gloss"]}
        amb_spans[span].append((ann["gloss"], ann['type'], span))
        span_list.append(span)
    span_list = sorted(span_list, key=lambda x: x[0])
    for i in range(len(span_list)-1):
        cur_span = span_list[i]
        next_span = span_list[i+1]
        if cur_span == next_span:
            result_spans[cur_span]["type"] = "full"
            f_ovlp_cnt += 1
        elif cur_span[1] > next_span[0]:
            result_spans[cur_span]["type"] = "part"
            result_spans[next_span]["type"] = "part"
        else:
            continue
    span_list_set = sorted([x for x in set(span_list) if result_spans[x]
                            is not "part"], key=lambda x: x[0])
    for span in span_list_set:
        if result_spans[span]["type"] != "none":
            print("Found it", span, result_spans[span], " text", text)
    if pick_random:
        tmp_set = [x for x in span_list_set]
        tot_random_mask = math.ceil(0.15*len(tmp_set))
        for i in range(tot_random_mask):
            random.shuffle(tmp_set)
            result_spans[tmp_set.pop()]["type"] = "full"
    # text_for_bert = text
    # if f_ovlp_cnt > 0:
    st_ind = 0
    text_tkns = []
    tot_masked = 0
    # print("rahulk", span_list_set)
    for i in range(len(span_list_set)):
        span = span_list_set[i]
        end_ind = span[0]
        text_tkns.append(text[st_ind:end_ind])
        if result_spans[span]["type"] == "full":
            text_tkns.append(" [MASK] ")
            tot_masked += 1
            # print("text %s gone with %s" % (text[span[0]:span[1]], "MASK"))
        else:
            text_tkns.append(" "+result_spans[span]["label"]+" ")
            # print("text %s gone with %s" % (text[span[0]:span[1]], result_spans[span]["label"]))
        st_ind = span[1]

    text_tkns.append(text[st_ind:])
    masked_result = []
    text_for_bert = re.sub(" +", " ", "".join(text_tkns)).strip()
    return text_for_bert, result_spans, span_list_set


def generate_replacement_data(data):
    id_fixed = data["id"]
    result_dataset = {}
    doc_cnt = 0
    for doc in data["sections"]:
        id = "%s_%d" % (id_fixed, doc_cnt)
        result_dataset[id] = {}
        doc_cnt += 1
        for d_typ in ["head", "body"]:
            if doc[d_typ]["annotations"]:
                text = doc[d_typ]["text"]
                # if not isinstance(text, str):
                #     print("byte mila")
                annotations = doc[d_typ]["annotations"]
                text_for_bert, spans, span_list_set = prepare_spans(
                    text, annotations, pick_random=True)
                result_dataset[id][d_typ] = {"text": text,
                                             "text_for_bert": text_for_bert,
                                             "spans": spans,
                                             "ordered_spans_set": span_list_set,
                                             "masked_output": []
                                             }
        print("Doc %3d processed" % (doc_cnt))
    return result_dataset


def get_annotations(ANNOTATED_JSON_FOLDER):
    relevant_types = {"disease": "disease", "Hugene": "gene", "Drug": "chemical"}
    predicted_annotations = {}
    for file in os.listdir(ANNOTATED_JSON_FOLDER):
        if not file.endswith(".json"):
            continue
        with open(os.path.join(ANNOTATED_JSON_FOLDER, file)) as f:
            data = json.load(f)
        id = file.split(".")[0]
        predicted_annotations[id] = {}
        for typ in data["sections"]:
            d_typ = typ["head"]["text"]
            predicted_annotations[id][d_typ] = []
            if typ["body"]["annotations"]:
                # predicted_annotations[id][d_typ].extend(typ["body"]["annotations"])
                for ann in typ["body"]["annotations"]:
                    if ann["type"] in relevant_types.keys():
                        tmp_dict = {"spans": ann["spans"], "type": relevant_types[ann["type"]],
                                    "gloss": ann["gloss"]}
                        predicted_annotations[id][d_typ].append(tmp_dict)
    return predicted_annotations


def generate_replacement_data_biocreative(root):
    result_dataset = {}
    doc_cnt = 0
    for child in root:
        if child.tag == "document":
            id = child.find("id").text
            # if id != "24114426":
            #     continue
            result_dataset[id] = {}
            doc_cnt += 1
            for psg in child.findall("passage"):
                d_typ = psg.find("infon").text
                offset_doc = int(psg.find("offset").text)
                text = psg.find("text").text
                annotations = []
                for ann in psg.findall("annotation"):
                    ann_pck = {}
                    for inf in ann.findall("infon"):
                        if inf.get("key") == "type":
                            ann_pck["type"] = inf.text.lower()
                    ann_pck["gloss"] = ann.find("text").text
                    loc = ann.find("location")
                    if (len(ann_pck["gloss"]) != int(loc.get("length"))):
                        print("\nGot it Gloss: %s Actual span Gloss %s\n" % (ann_pck["gloss"],
                                                                             text[(int(loc.get("offset"))-offset_doc):
                                                                                  (int(loc.get("offset"))-offset_doc+int(loc.get("length")))]))
                    ann_pck["spans"] = [(int(loc.get("offset"))-offset_doc,
                                         int(loc.get("offset"))-offset_doc+int(loc.get("length")))]
                    annotations.append(ann_pck)
                if annotations:
                    text_for_bert, spans, span_list_set = prepare_spans(
                        text, annotations, pick_random=True)
                    result_dataset[id][d_typ] = {"text": text,
                                                 "text_for_bert": text_for_bert,
                                                 "spans": spans,
                                                 "ordered_spans_set": span_list_set,
                                                 "masked_output": []
                                                 }

            print("Doc %3d processed" % (doc_cnt))
    return result_dataset


def generate_replacement_data_annotated(GROUND_TRUTH_FILE, ANNOTATED_JSON_FOLDER):
    with open(GROUND_TRUTH_FILE, "rb") as f:
        input_dataset = pickle.load(f)
    predicted_annotations = get_annotations(ANNOTATED_JSON_FOLDER)
    result_dataset = {}
    for id in input_dataset.keys():
        result_dataset[id] = {}
        for d_typ in input_dataset[id].keys():
            annotations = predicted_annotations[id][d_typ]
            ground_truth = input_dataset[id][d_typ]["spans"]
            text = input_dataset[id][d_typ]["text"]
            text_for_bert = ""
            spans = {}
            span_list_set = []
            if annotations:
                text_for_bert, spans, span_list_set = prepare_spans(
                    text, annotations, pick_random=False)
            result_dataset[id][d_typ] = {"text": text,
                                         "text_for_bert": text_for_bert,
                                         "spans": spans,
                                         "ordered_spans_set": span_list_set,
                                         "ground_truth": ground_truth,
                                         "masked_output": []
                                         }
    return result_dataset


def write_dataset_pickle(result_dataset, out_folder):
    with open(os.path.join(out_folder, "result_dataset.pkl"), "wb") as f:
        pickle.dump(result_dataset, f)


def write_dataset_json(result_dataset, out_folder):
    with open(os.path.join(out_folder, "result_dataset.json"), "w") as f:
        json.dump(result_dataset, f)


def main(file_list_path):
    JSON_FILE_LIST = []
    for file_name in open(file_list_path):
        data = json.load(open(file_name))
        generate_replacement_data(data)
        create_classification_data(data)


if __name__ == "__main__":
    # file = "/Users/rahulpandey/Downloads/George/JsonCTDs_NlpAnnotated/NCT03171805.json"
    # file = "/Users/rahulpandey/Downloads/George/JsonCTDs_NlpAnnotated/NCT00117936.json"
    # file_cdr = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/data/CDR_Data/CDR.Corpus.v010516/CDR_TestSet.BioC.xml"
    # data = json.load(open(file, "r"))
    # tree = ET.parse(file_cdr)
    # root = tree.getroot()
    ANNOTATED_JSON_FOLDER = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/data/JsonCTDs_NlpAnnotated/"
    GROUND_TRUTH_FILE = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/data/bert-ready/cdr_data_new/result_dataset.pkl"
    result_dataset = generate_replacement_data_annotated(GROUND_TRUTH_FILE, ANNOTATED_JSON_FOLDER)
    out_folder = os.path.join(os.getcwd(), "data", "bert-ready", "cdr_data_annotated_actual")
    if not os.path.isdir(out_folder):
        os.makedirs(out_folder)
    write_dataset_pickle(result_dataset, out_folder)
    # write_dataset_json(result_dataset, out_folder)
