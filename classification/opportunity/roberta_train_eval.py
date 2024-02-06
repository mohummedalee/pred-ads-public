import os, sys
from datetime import datetime

import datasets
import numpy as np
import pandas as pd

from transformers import Trainer, TrainingArguments
from transformers import RobertaForSequenceClassification, RobertaTokenizer
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix


seed = 42 
tokenizer = None
model_type = "roberta-base"  # Type of model to fine tune
model = None


def load_data(fpath, save_splits=True):
    global tokenizer, model_type, seed

    raw_csv = pd.read_csv(fpath)
    print("Loaded csv shape:", raw_csv.shape)
    print("Loaded csv columns:", raw_csv.columns)

    labels = raw_csv["opportunity"].values.astype(np.int8)
    texts = raw_csv["text"].values.astype(str)
    assert labels.shape[0] == texts.shape[0]

    # convert to huggingface dataset
    data = datasets.Dataset.from_dict({"text": texts, "label": labels})
    split = data.train_test_split(test_size=0.2, seed=seed)
    train_data = split["train"]
    val_data = split["test"]

    if save_splits:
        train_data.to_csv('opportunity_train.csv')
        val_data.to_csv('opportunity_val.csv')

    # set up tokenizer
    tokenizer = RobertaTokenizer.from_pretrained(model_type)
    print("Tokenizer details: ", tokenizer)
    # if compute is limited :(
    tokenizer.model_max_length = 128

    # tokenize training data
    train_data = train_data.map(
        lambda x: tokenizer(x["text"], truncation=True, padding="max_length"),
        batched=True
    )
    train_data.set_format("torch", columns=["input_ids", "attention_mask", "label"])
    train_data = train_data.remove_columns("text")
    # tokenize validation data
    val_data = val_data.map(
        lambda x: tokenizer(x["text"], truncation=True, padding="max_length"),
        batched=True
    )
    val_data.set_format("torch", columns=["input_ids", "attention_mask", "label"])
    val_data = val_data.remove_columns("text")

    return train_data, val_data


def train_roberta_classifier(train_data, val_data):
    global tokenizer, seed, model, model_type
    
    device = "cuda"

    # set up model w/ classification head
    model = RobertaForSequenceClassification.from_pretrained(model_type, num_labels=2)
    model = model.to(device)    

    # run trainer on model
    training_args = TrainingArguments(
        optim="adamw_torch",
        logging_steps=50,
        output_dir="../temp_data",
        per_device_eval_batch_size=64,
        per_device_train_batch_size=64,
        report_to="none",
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=val_data,
    )

    trainer.train()
    trainer.save_model(output_dir=os.path.join("../temp_data", "final"))
    trainer.save_state()

    return trainer


def evaluate_model(trainer, val_data):    
    preds = trainer.predict(val_data)
    preds_labels = np.argmax(preds.predictions, axis=1)
    val_labels = val_data["label"].numpy()

    # log to file
    temp = sys.stdout
    with open('roberta_eval.log', 'a') as wh:
        sys.stdout = wh
        print("Accuracy:", accuracy_score(val_labels, preds_labels))
        print("F1:", f1_score(val_labels, preds_labels))
        print("Classification report:\n", classification_report(val_labels, preds_labels))
        print("Confusion matrix:\n", confusion_matrix(val_labels, preds_labels))
        # revert
        sys.stdout = temp


if __name__ == '__main__':
    print('Loading + preprocessing data...')    
    train_data, val_data = load_data('data/text_data_annotated.csv')

    print('Training model...')
    trainer = train_roberta_classifier(train_data, val_data)

    print('Evaluating on validation data...')
    evaluate_model(trainer, val_data)